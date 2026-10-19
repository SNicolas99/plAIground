import pytest

from app.core.interfaces import Agent, GameEngine


def test_cannot_instantiate_abstract_engine():
    with pytest.raises(TypeError):
        GameEngine()


def test_cannot_instantiate_abstract_agent():
    with pytest.raises(TypeError):
        Agent()
