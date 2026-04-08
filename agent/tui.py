from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList, Static
from textual.widgets.option_list import Option

class NumberedMenuApp(App):

    def compose(self) -> ComposeResult:
        yield Header()
        # OptionList provides the "highlight and press enter" behavior
        yield OptionList(
            Option("1. Start Application", id="start"),
            Option("2. View Database", id="view"),
            Option("3. Exit System", id="exit"),
            id="menu"
        )
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Called when user highlights an option and presses Enter."""
        option_id = event.option.id
        
        # Mapping IDs to specific function calls
        actions = {
            "start": self.action_start,
            "view": self.action_view,
            "exit": self.exit_app
        }
        
        action_func = actions.get(option_id)
        if action_func:
            action_func()

    # --- Your Functions ---
    def action_start(self):
        self.notify("Starting the engine...")

    def action_view(self):
        self.notify("Accessing database records...")

    def exit_app(self):
        self.exit()

if __name__ == "__main__":
    app = NumberedMenuApp()
    app.run()
