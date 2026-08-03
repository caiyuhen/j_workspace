from app.services.events import EventBroker


def test_project_creation_publishes_event() -> None:
    broker = EventBroker()

    broker.publish("project.created", {"workspace_key": "demo-hospital/糖尿病真实世界研究"})

    assert broker.drain() == [
        {
            "event_type": "project.created",
            "payload": {"workspace_key": "demo-hospital/糖尿病真实世界研究"},
        }
    ]
