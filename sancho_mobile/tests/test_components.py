import flet as ft
from sancho_mobile.views.components.chat_bubble import chat_bubble, ChatBubble
from sancho_mobile.views.components.thought_bubble import thought_bubble, ThoughtBubble
from sancho_mobile.views.components.tool_card import ToolCard

def test_chat_bubble_creation_and_scale():
    cb = chat_bubble("Hello", is_user=True)
    assert isinstance(cb, ChatBubble)
    assert cb.base_text == "Hello"
    assert cb.font_scale == 1.0
    
    cb.update_font_scale(1.2)
    assert cb.font_scale == 1.2
    
    cb.update_text("Hello World")
    assert cb.base_text == "Hello World"

def test_thought_bubble_creation_and_update():
    tb = thought_bubble("Initial thought")
    assert isinstance(tb, ThoughtBubble)
    assert tb.thought_text_control.value == "Initial thought"
    
    tb.update_thought("Updated thought")
    assert tb.thought_text_control.value == "Updated thought"
    
    tb.update_font_scale(1.35)
    assert tb.font_scale == 1.35
    assert tb.thought_text_control.size == 12.5 * 1.35

def test_tool_card_creation_and_update():
    tc = ToolCard("get_topological_map", "call_123")
    assert tc.tool_name == "get_topological_map"
    assert tc.tool_call_id == "call_123"
    assert tc.font_scale == 1.0
    
    # Check initial values
    assert tc.status_text.value == "Executing..."
    
    # Update progress and result
    tc.update_progress(
        status="completed",
        title="Get Topological Map",
        progress_text="Mapping points...",
        raw_output="{'kitchen': (1, 2)}"
    )
    
    assert tc.status_text.value == "Completed"
    
    # Verify collapsing / expanding toggle state
    assert tc.output_expanded is False
    assert tc.details_column.controls[-1].visible is False
    
    # Trigger toggle expansion
    tc.toggle_output_visibility(None)
    assert tc.output_expanded is True
    assert tc.details_column.controls[-1].visible is True
    
    # Check scaling updates
    tc.update_font_scale(1.2)
    assert tc.font_scale == 1.2
    assert tc.title_text.size == 13 * 1.2
