import itertools
from enum import Enum
from pydantic import BaseModel

class Language(str, Enum):
    IT = 'Italian'
    EN = 'English'
    RU = "Russian"

class Task(BaseModel):
    """A data class that represent a sigle task"""
    language: Language = Language.IT
    template: str = ""
    targs: dict[str, list[str]] = None
    context: str = None

def generate_prompts(task: Task) -> list[str]:
    """Given a Task instance, uses its template and optional
    args, interpolates the final strings and returns a list of
    prompts ready for submission."""

    prompts = []
    
    if task.targs:
        combinations = list(itertools.product(*task.targs.values()))

        for comb in combinations:
            comb_dict = dict(zip(task.targs.keys(), comb))
            prompt = task.template.format(**comb_dict)

            prompts.append(prompt)
    else:
        prompt = task.template
        prompts.append(prompt)

    # add context, if applicable
    if(task.context and task.context != ""):
        prompts = list(map(lambda x: f"""{x}\n\n{task.context}""", prompts))

    return prompts