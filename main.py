from schedular import Schedular
import typer
import google.generativeai as genai
from dotenv import load_dotenv
import os
from prompts import Prompts
import json
import ast
from rich.console import Console
from rich.markdown import Markdown
from config import Config


load_dotenv()

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

app = typer.Typer()
console = Console()


class Main:
    def __init__(self) -> None:
        self._schedular = Schedular()
        self._db = Config.DB_PATH
        self._generative_model = genai.GenerativeModel(
            Config.GEMINI_MODEL_NAME, generation_config={"temperature": 0.0}
        )

    def schedule_cron_job(self, schedule_time: str = "* * * * *"):
        self._schedular.schedule_cron_job(schedule_time)
        typer.echo("Job successfully scheduled")

    def format_markdown_table(self, headers, values) -> str:
        column_widths = [
            max(len(str(item)) for item in col) for col in zip(headers, *values)
        ]
        formatted_table = (
            "| "
            + " | ".join(
                f"{header.ljust(width)}"
                for header, width in zip(headers, column_widths)
            )
            + " |\n"
        )
        formatted_table += (
            "|-" + "-|-".join("-" * width for width in column_widths) + "-|\n"
        )
        for row in values:
            formatted_table += (
                "| "
                + " | ".join(
                    f"{str(item).ljust(width)}"
                    for item, width in zip(row, column_widths)
                )
                + " |\n"
            )

        return formatted_table

    def reschedule_cron_job(self, reschedule_time: str = "* 1 * * *"):
        self._schedular.reschedule_cron_job(reschedule_time)
        typer.echo("Job scheduled successfully")

    def remove_cron_job(self):
        self._schedular.remove_cron_job()
        typer.echo("Job removed successfully")

    def format_string(self, s: str):
        return s.replace("```", "").replace("json", "")

    def chat_with_os(
        self,
        user_query: str = "Provide me the top 10 running task along with the resources",
    ):
        response = self._generative_model.generate_content(
            Prompts.DB_PROMPT.format(
                schemas=self._db.get_table_info(), user_query=user_query
            )
        )
        try:
            formatted_string = self.format_string(response.text)
            json_data = json.loads(formatted_string)

            # Assuming `self._db.run()` returns a JSON formatted string
            result = self._db.run(json_data["sql_query"])

            values = ast.literal_eval(result)

            final_answer = self.format_markdown_table(
                json_data["column_headers"], values
            )

            md = Markdown(final_answer)

            console.print(md)

        except json.JSONDecodeError as e:
            md = Markdown(response.text)
            console.print(md)
        except KeyError as e:
            print(f"Key error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


cli_app = Main()

app.command()(cli_app.schedule_cron_job)
app.command()(cli_app.reschedule_cron_job)
app.command()(cli_app.remove_cron_job)
app.command()(cli_app.chat_with_os)


if __name__ == "__main__":
    app()
