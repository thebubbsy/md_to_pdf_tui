from textual.app import App
import sys

class TestApp(App):
    def on_mount(self):
        try:
            if hasattr(self, 'notify'):
                self.notify("Hello World")
                print("Notify success")
            else:
                print("Notify not available")
        except Exception as e:
            print(f"Error: {e}")
        self.exit()

if __name__ == "__main__":
    TestApp().run()
