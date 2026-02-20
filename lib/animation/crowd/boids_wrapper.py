"""
Boids Wrapper for Blender's Built-in Particle System

Provides a high-level interface for creating and configuring boid simulations.

Phase 13.5: Crowd System (REQ-ANIM-07)
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from ..types import (
    CrowdConfig,
    BoidRuleConfig,
    BoidSettingsConfig,
    BehaviorState,
    MAX_PARTICLE_COUNT,
    WARN_PARTICLE_COUNT,
)


class BoidsWrapper:
    """Wrapper for Blender's built-in boids particle system."""

    # Valid boid rule types
    VALID_RULES = {
        'GOAL',
        'AVOID',
        'AVOID_COLLISION',
        'SEPARATE',
        'FLOCK',
        'FOLLOW_LEADER',
        'AVERAGE_SPEED',
        'FIGHT',
        'FOLLOW_CURVE',
        'FOLLOW_WALL',
    }

    def __init__(self, particle_system=None):
        """Initialize the boids wrapper.

        Args:
            particle_system: Optional existing particle system to wrap
        """
        self._particle_system = particle_system
        self._rules: List[BoidRuleConfig] = []

    @property
    def particle_system(self):
        """Get the wrapped particle system."""
        return self._particle_system

    @staticmethod
    def create_emitter(
        name: str = "BoidEmitter",
        location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        size: float = 10.0
    ):
        """Create a plane mesh to use as particle emitter.

        Args:
            name: Name for the emitter object
            location: World location for the emitter
            size: Size of the emitter plane

        Returns:
            The created emitter object (mock for testing)
        """
        # This would create a Blender plane in real usage
        # For testing without bpy, we return a mock-like dict
        return {
            'name': name,
            'location': location,
            'size': size,
            'type': 'MESH',
        }

    @staticmethod
    def create_boids_system(
        emitter,
        name: str = "Boids",
        particle_count: int = 100,
        render_type: str = 'OBJECT',
        agent_object: Optional[Any] = None
    ):
        """Create a boids particle system on an emitter.

        Args:
            emitter: The emitter object
            name: Name for the particle system
            particle_count: Number of particles
            render_type: How to render particles ('OBJECT', 'COLLECTION', 'PATH', 'NONE')
            agent_object: Object to instance for each boid

        Returns:
            BoidsWrapper instance with the created system
        """
        # Validate particle count
        if particle_count > MAX_PARTICLE_COUNT:
            raise ValueError(
                f"Particle count {particle_count} exceeds maximum {MAX_PARTICLE_COUNT}. "
                "Consider splitting into multiple systems."
            )

        if particle_count > WARN_PARTICLE_COUNT:
            import warnings
            warnings.warn(
                f"Particle count {particle_count} is high. Performance may be affected.",
                UserWarning
            )

        # Create mock particle system for testing
        ps = {
            'name': name,
            'count': particle_count,
            'render_type': render_type,
            'agent_object': agent_object,
            'physics_type': 'BOIDS',
            'rules': [],
            'settings': BoidSettingsConfig().to_dict(),
        }

        return BoidsWrapper(ps)

    def set_agent_object(self, obj) -> None:
        """Set the object to render for each boid.

        Args:
            obj: The object to instance for each boid
        """
        if self._particle_system:
            self._particle_system['agent_object'] = obj

    def set_behavior_rules(self, rules: List[Tuple[str, float]]) -> None:
        """Set boid behavior rules with weights.

        Args:
            rules: List of (rule_type, weight) tuples
        """
        self._rules = []

        for rule_type, weight in rules:
            rule_type_upper = rule_type.upper()
            if rule_type_upper not in self.VALID_RULES:
                raise ValueError(f"Invalid rule type: {rule_type}. Valid types: {self.VALID_RULES}")

            self._rules.append(BoidRuleConfig(
                rule_type=rule_type_upper,
                weight=weight,
            ))

        if self._particle_system:
            self._particle_system['rules'] = [r.to_dict() for r in self._rules]

    def add_rule(self, rule: BoidRuleConfig) -> None:
        """Add a single boid rule.

        Args:
            rule: The rule configuration to add
        """
        if rule.rule_type.upper() not in self.VALID_RULES:
            raise ValueError(f"Invalid rule type: {rule.rule_type}")

        self._rules.append(rule)
        if self._particle_system:
            self._particle_system['rules'] = [r.to_dict() for r in self._rules]

    def clear_rules(self) -> None:
        """Clear all behavior rules."""
        self._rules = []
        if self._particle_system:
            self._particle_system['rules'] = []

    def get_rules(self) -> List[BoidRuleConfig]:
        """Get all configured rules."""
        return self._rules.copy()

    def configure_boid_settings(self, settings: BoidSettingsConfig) -> None:
        """Configure boid physics settings.

        Args:
            settings: The boid settings to apply
        """
        if self._particle_system:
            self._particle_system['settings'] = settings.to_dict()

    def get_boid_settings(self) -> BoidSettingsConfig:
        """Get current boid settings."""
        if self._particle_system and 'settings' in self._particle_system:
            return BoidSettingsConfig.from_dict(self._particle_system['settings'])
        return BoidSettingsConfig()

    # Preset behaviors

    def add_flock_behavior(self) -> None:
        """Add standard flocking behavior (separate, align, cohesion)."""
        self.set_behavior_rules([
            ('SEPARATE', 1.0),
            ('FLOCK', 0.8),
            ('AVERAGE_SPEED', 0.5),
            ('AVOID_COLLISION', 1.0),
        ])

    def add_swarm_behavior(self, target=None) -> None:
        """Add swarming behavior around a target.

        Args:
            target: Optional target object to swarm around
        """
        rules = [
            ('GOAL', 1.5),
            ('SEPARATE', 0.8),
            ('AVERAGE_SPEED', 0.3),
        ]

        if target:
            goal_rule = BoidRuleConfig(
                rule_type='GOAL',
                weight=1.5,
                target_object=target.name if hasattr(target, 'name') else str(target),
            )
            self.clear_rules()
            self.add_rule(goal_rule)
            for rule_type, weight in rules[1:]:
                self.add_rule(BoidRuleConfig(rule_type=rule_type, weight=weight))
        else:
            self.set_behavior_rules(rules)

    def add_herd_behavior(self, leader=None) -> None:
        """Add herding/following behavior.

        Args:
            leader: Optional leader object to follow
        """
        if leader:
            self.clear_rules()
            self.add_rule(BoidRuleConfig(
                rule_type='FOLLOW_LEADER',
                weight=2.0,
                target_object=leader.name if hasattr(leader, 'name') else str(leader),
                distance=2.0,
            ))
            self.add_rule(BoidRuleConfig(rule_type='SEPARATE', weight=0.5))
            self.add_rule(BoidRuleConfig(rule_type='AVOID_COLLISION', weight=1.0))
        else:
            self.set_behavior_rules([
                ('SEPARATE', 0.5),
                ('FLOCK', 1.0),
                ('AVOID_COLLISION', 0.8),
            ])

    def add_follow_path_behavior(self, curve) -> None:
        """Add follow path behavior.

        Args:
            curve: The curve object to follow
        """
        self.add_rule(BoidRuleConfig(
            rule_type='FOLLOW_CURVE',
            weight=2.0,
            target_object=curve.name if hasattr(curve, 'name') else str(curve),
        ))

    def add_avoid_behavior(self, obstacle=None) -> None:
        """Add avoidance behavior.

        Args:
            obstacle: Optional obstacle to avoid
        """
        rule = BoidRuleConfig(
            rule_type='AVOID',
            weight=1.5,
        )
        if obstacle:
            rule.target_object = obstacle.name if hasattr(obstacle, 'name') else str(obstacle)
        self.add_rule(rule)

    def set_land_mode(self) -> None:
        """Configure boids for land-based movement (walking creatures)."""
        settings = BoidSettingsConfig(
            use_flight=False,
            use_land=True,
            use_climb=False,
            land_speed_max=2.0,
            land_acc_max=0.5,
            land_personal_space=1.0,
        )
        self.configure_boid_settings(settings)

    def set_flight_mode(self) -> None:
        """Configure boids for flying (birds, insects)."""
        settings = BoidSettingsConfig(
            use_flight=True,
            use_land=False,
            use_climb=False,
            air_speed_min=5.0,
            air_speed_max=15.0,
            air_acc_max=1.0,
        )
        self.configure_boid_settings(settings)

    def set_both_mode(self) -> None:
        """Configure boids for both flying and landing."""
        settings = BoidSettingsConfig(
            use_flight=True,
            use_land=True,
            use_climb=True,
        )
        self.configure_boid_settings(settings)

    def apply_crowd_config(self, config: CrowdConfig) -> None:
        """Apply a crowd configuration to this boid system.

        Args:
            config: The crowd configuration to apply
        """
        # Set particle count
        if self._particle_system:
            self._particle_system['count'] = config.spawn.count

        # Configure based on crowd type
        if config.crowd_type.value == 'creature':
            # Flying creatures by default for creature type
            self.set_flight_mode()
        else:
            # Pedestrians, audience, vehicles use land mode
            self.set_land_mode()

        # Apply behavior rules based on crowd type
        self.clear_rules()

        if config.crowd_type.value == 'pedestrian':
            self.add_rule(BoidRuleConfig(rule_type='SEPARATE', weight=1.0))
            self.add_rule(BoidRuleConfig(rule_type='AVOID_COLLISION', weight=1.5))
            self.add_rule(BoidRuleConfig(rule_type='AVERAGE_SPEED', weight=0.3))
        elif config.crowd_type.value == 'creature':
            self.add_flock_behavior()

    def to_dict(self) -> Dict[str, Any]:
        """Export boid configuration to dictionary."""
        return {
            'particle_system': self._particle_system,
            'rules': [r.to_dict() for r in self._rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoidsWrapper':
        """Create wrapper from dictionary."""
        wrapper = cls(data.get('particle_system'))
        wrapper._rules = [BoidRuleConfig.from_dict(r) for r in data.get('rules', [])]
        return wrapper


# Convenience functions

def create_flock(
    name: str,
    agent_object: Any,
    count: int = 50,
    leader: Optional[Any] = None
) -> BoidsWrapper:
    """Create a flock of agents using boids.

    Args:
        name: Name for the particle system
        agent_object: Object to instance for each flock member
        count: Number of flock members
        leader: Optional leader object to follow

    Returns:
        Configured BoidsWrapper instance
    """
    emitter = BoidsWrapper.create_emitter(f"{name}_emitter")
    wrapper = BoidsWrapper.create_boids_system(
        emitter=emitter,
        name=name,
        particle_count=count,
        render_type='OBJECT',
        agent_object=agent_object
    )

    if leader:
        wrapper.add_herd_behavior(leader=leader)
    else:
        wrapper.add_flock_behavior()

    wrapper.set_flight_mode()
    return wrapper


def create_swarm(
    name: str,
    agent_object: Any,
    count: int = 100,
    target: Optional[Any] = None
) -> BoidsWrapper:
    """Create a swarm of agents around a target.

    Args:
        name: Name for the particle system
        agent_object: Object to instance for each swarm member
        count: Number of swarm members
        target: Optional target to swarm around

    Returns:
        Configured BoidsWrapper instance
    """
    emitter = BoidsWrapper.create_emitter(f"{name}_emitter")
    wrapper = BoidsWrapper.create_boids_system(
        emitter=emitter,
        name=name,
        particle_count=count,
        render_type='OBJECT',
        agent_object=agent_object
    )

    wrapper.add_swarm_behavior(target=target)
    wrapper.set_flight_mode()
    return wrapper


def create_herd(
    name: str,
    agent_object: Any,
    count: int = 30,
    leader: Optional[Any] = None
) -> BoidsWrapper:
    """Create a herd of ground-based agents.

    Args:
        name: Name for the particle system
        agent_object: Object to instance for each herd member
        count: Number of herd members
        leader: Optional leader object to follow

    Returns:
        Configured BoidsWrapper instance
    """
    emitter = BoidsWrapper.create_emitter(f"{name}_emitter")
    wrapper = BoidsWrapper.create_boids_system(
        emitter=emitter,
        name=name,
        particle_count=count,
        render_type='OBJECT',
        agent_object=agent_object
    )

    wrapper.add_herd_behavior(leader=leader)
    wrapper.set_land_mode()
    return wrapper
