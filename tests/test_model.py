from ccproxy import model
from pydantic import ValidationError
import pytest

class TestConfig:
    def test_config_validation_missing_messages(self) -> None:
        config = {
            'messages': {
            },
            'actions': {
                'foo_action': 'foo_action_path',
                'bar_action': 'bar_action_path'
            }
        }

        with pytest.raises(ValidationError, match='Missing messages for the following actions: foo_action, bar_action'):
            model.Config(**config)

    def test_config_validation_empty_path(self) -> None:
        config = {
            'messages': {
                'foo_action': ['foo message'],
                'bar_action': ['bar message']
            },
            'actions': {
                'foo_action': '',
                'bar_action': ''
            }
        }

        with pytest.raises(ValidationError, match='Path is empty for the following actions: foo_action, bar_action'):
            model.Config(**config)

    def test_config_validation_empty_messages(self) -> None:
        config = {
            'messages': {
                'foo_action': [],
                'bar_action': []
            },
            'actions': {
                'foo_action': 'foo path',
                'bar_action': 'bar path'
            }
        }

        with pytest.raises(ValidationError, match='Messages are not provided for the following actions: foo_action, bar_action'):
            model.Config(**config)