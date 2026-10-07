"""Tests for EventBus (basic tests only, full tests require Redis)."""


from shared.events.bus import EventBus, get_event_bus


class TestEventBusInit:
    """Tests for EventBus initialization."""
    
    def test_init_default_values(self):
        bus = EventBus()
        
        assert bus.redis_url == "redis://localhost:6379"
        assert bus.source_service == ""
        assert bus.is_connected is False
    
    def test_init_custom_values(self):
        bus = EventBus(
            redis_url="redis://custom:6379",
            source_service="my-service",
        )
        
        assert bus.redis_url == "redis://custom:6379"
        assert bus.source_service == "my-service"


class TestEventBusHandlerRegistration:
    """Tests for handler registration."""
    
    def test_subscribe(self):
        bus = EventBus()
        
        async def handler(event):
            pass
        
        bus.subscribe("work_order.created", handler)
        
        assert "events:work_order.created" in bus._handlers
        assert len(bus._handlers["events:work_order.created"]) == 1
    
    def test_subscribe_pattern(self):
        bus = EventBus()
        
        async def handler(event):
            pass
        
        bus.subscribe_pattern("work_order.*", handler)
        
        assert "events:work_order.*" in bus._handlers
    
    def test_multiple_handlers_for_same_event(self):
        bus = EventBus()
        
        async def handler1(event):
            pass
        
        async def handler2(event):
            pass
        
        bus.subscribe("work_order.created", handler1)
        bus.subscribe("work_order.created", handler2)
        
        assert len(bus._handlers["events:work_order.created"]) == 2


class TestGetEventBus:
    """Tests for get_event_bus helper."""
    
    def test_get_event_bus_creates_instance(self):
        # Reset by setting global to None
        import shared.events.bus as bus_module
        bus_module._event_bus = None
        
        bus = get_event_bus(source_service="test-service")
        
        assert bus is not None
        assert bus.source_service == "test-service"
        
        # Cleanup
        bus_module._event_bus = None
    
    def test_get_event_bus_returns_same_instance(self):
        import shared.events.bus as bus_module
        bus_module._event_bus = None
        
        bus1 = get_event_bus(source_service="service1")
        bus2 = get_event_bus(source_service="service2")
        
        # Should return the same instance
        assert bus1 is bus2
        # First service name should be kept
        assert bus1.source_service == "service1"
        
        # Cleanup
        bus_module._event_bus = None


class TestEventBusProperties:
    """Tests for EventBus properties."""
    
    def test_is_connected_false_initially(self):
        bus = EventBus()
        assert bus.is_connected is False
    
    def test_is_listening_false_initially(self):
        bus = EventBus()
        assert bus.is_listening is False
