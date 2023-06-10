#!/usr/bin/env python3

from loguru import logger
from pydantic import BaseModel, Field, ValidationError
from typing import Any, Optional, List
import os
import openai
import json 
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text


class Task(BaseModel):
    description      : str                       = Field(description="The detailed description of the task we are performing.")
    filenames        : list[str]                 = Field(description="The full list of existing file names with relevant content that are available to read to help accomplish the task.")
    work_summary     : str                       = Field(description="A summary of the work we have done so far to try to accomplish the task.")
    notes            : Optional[str]             = Field(description="Any notes about the task that might be helpful to remember.")
    next_step_hint   : Optional[str]             = Field(description="A description of a possible next step to take to accomplish the task.")
    read_files       : Optional[dict[str, str]]  = Field(description="A dictionary of filenames and their content that were just read to help accomplish the next step.")
    coworker_message : Optional[str]             = Field(description="A message from a coworker to help accomplish the task.")
    step             : int                       = Field(description="The number of steps we have taken so far to try to accomplish the task.")

    def __str__(self) -> str:
        outstr = "\nPairWise Task State:\n\n"
        outstr += f"Description:  {self.description}\n"
        outstr += f"Work Summary: {self.work_summary}\n"
        if self.notes:
            outstr += f"Notes:        {self.notes}\n"
        if self.next_step_hint:
            outstr += f"Next Step:    {self.next_step_hint}\n"
        if self.read_files:
            outstr += f"Read Files:   {self.read_files.keys()}\n"
        if self.coworker_message:
            outstr += f"Coworker Msg: {self.coworker_message}\n"
        outstr += f"Filenames:    {len(self.filenames)} files\n"
        outstr += f"Step:         {self.step}\n"
        return outstr
    
class CreateFile(BaseModel):
    filename  : str  = Field(..., description="The name of a file to create to help accomplish the task. Must not be an existing filename.")
    content   : str  = Field(..., description="The content to write to the filename to help accomplish the task.")        

    
class NextStep(BaseModel):
    create_file      : Optional[CreateFile] = Field(description="An optional file to create to help accomplish the task.")    
    work_summary     : str                  = Field(description="The updated summary of the work we have done so far to accomplish the task, not including files we have read.")    
    notes            : Optional[str]        = Field(description="Any notes about the task that might be helpful to remember.")    
    read_filenames   : Optional[list[str]]  = Field(description="A list of filenames to read to help perform the next step.")    
    ask_question     : Optional[str]        = Field(description="An optional question to ask a coworker to help accomplish the task. Use this option if you are not sure what the next step is.")
    next_step_hint   : Optional[str]        = Field(description="A description of the anticipated next step to take to accomplish the task.")
    task_done        : Optional[bool]       = Field(description="true if the task is complete")
    
    def __str__(self):
        outstr = "\nPairWise Next Step:\n\n"
        if self.create_file:
            outstr += f"CREATE FILE:     {self.create_file.filename}\n"
            outstr += f"===============  File Content ===============\n"
            outstr += self.create_file.content
            outstr += f"\n===============  End  Content ===============\n"
        outstr += f"Work Summary: {self.work_summary}\n"
        if self.notes:
            outstr += f"Notes: {self.notes}\n"
        if self.next_step_hint:
            outstr += f"Next Step Hint: {self.next_step_hint}\n"
        if self.ask_question:
            outstr += f"Ask Question:   {self.ask_question}\n"
        if self.read_filenames:
            outstr += f"Read Filenames: {self.read_filenames}\n"
        if  self.task_done:
            outstr += f"Task Done:      {self.task_done}\n"
        return outstr

    

SYSTEM_PROMPT = f"""
You are a capable assistant that is working to accomplish a complex multi-step task.
The full task is provided below in json form.  The json_schema of the task description is: {Task.schema_json()}.
You will output in json form the next step of the task as described below.
As a next step you have options to read files, create files, and ask questions to help accomplish the task.
Please set the task_done field to true when the task is complete.
The task description follows in json.
"""

def find_files(file_extensions = ('.py', '.md', '.txt')):  
    path = os.getcwd()    
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(file_extensions):
                rel_path = os.path.relpath(os.path.join(root, file), path)
                file_paths.append(rel_path)
    return file_paths



def task_prompt(task: Task) -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "system", "content": task.json()}]

    

def create(messages : List[dict], model_class: BaseModel, retry=2, temperature=0, **kwargs) -> BaseModel:

    messages.append({"role"   : "system",
                     "content": f"Please respond ONLY with valid json that conforms to this pydantic json_schema: {model_class.schema_json()}. Do not include additional text other than the object json as we will load this object with json.loads() and pydantic."})

    last_exception = None
    for i in range(retry+1):
        response = openai.ChatCompletion.create(messages=messages, temperature=temperature, **kwargs)
        assistant_message= response['choices'][0]['message']
        content = assistant_message['content']
        try:
            json_content = json.loads(content.strip())
        except Exception as e:
            last_exception = e
            error_msg = f"json.loads exception: {e}"
            logger.error(error_msg)
            logger.error(content)
            messages.append(assistant_message)
            messages.append({"role"   : "system",
                            "content": error_msg})
            continue
        try:
            return model_class(**json_content)
        except ValidationError as e:
            last_exception = e
            error_msg = f"pydantic exception: {e}"
            logger.error(error_msg)
            messages.append(assistant_message)
            messages.append({"role"   : "system",
                            "content": error_msg})    
    raise last_exception


DEFAULT_NEXT_STEP_HINT = "Think through how to break the task up into smaller tasks and save the steps in the notes."
            
def perform_task(task_description : str,
                 next_step_hint   : str = DEFAULT_NEXT_STEP_HINT) -> None:
    
    task = Task(description=task_description, 
                next_step_hint=next_step_hint,
                filenames=find_files(), 
                work_summary="",
                step=0)
    
    while True:

        print(str(task))
       
        messages = task_prompt(task)
                            
        next_step = create(messages, NextStep, retry=4, temperature=.02, model='gpt-4')    

        print_formatted_text(FormattedText([("fg:darkred", str(next_step))]))

        do_continue = input("Proceed? (Y/n): ")        
        if do_continue and do_continue.lower()[0] == 'n':
            break
                       
        # create file if needed
        if next_step.create_file:
            print_formatted_text(FormattedText([("fg:MediumVioletRed", f"\n[Creating file {next_step.create_file.filename}]\n")]))
            if next_step.create_file.filename.split('.')[-1] not in ['py', 'md', 'txt']:
              raise Exception(f"filename {next_step.create_file.filename} must have a valid file extension") 
            if next_step.create_file.filename in task.filenames:
                print_formatted_text(FormattedText([("fg:red", f"WARNING: filename {next_step.create_file.filename} already exists\n")]))
                do_continue = input(f"Overwrite? (Y/n): ")        
                if do_continue and do_continue.lower()[0] == 'n':
                    break                
            open(next_step.create_file.filename, 'w').write(next_step.create_file.content)            

        if next_step.task_done:
            print_formatted_text(FormattedText([("fg:MediumVioletRed", "DONE: task_done is set\n")]))
            break
    
        if next_step.ask_question:
            print(next_step.ask_question)
            raise NotImplementedError("need to implement asking a question")

        # update state
        task.work_summary = next_step.work_summary
        task.notes        = next_step.notes
        task.next_step_hint = next_step.next_step_hint
        
        # read the requested files
        task.filenames = find_files()
        for fn in next_step.read_filenames:
            if fn not in task.filenames:
                raise Exception(f"read filename {fn} not found in filenames")            
        task.read_files = {fn : open(fn).read() for fn in next_step.read_filenames}

        task.step += 1
        # check if the context is likely too large and prompt the model to break up the next step

if __name__ == "__main__":
    #perform_task("create a file named 'test.txt' with the content 'hello world'")
    #perform_task('create a file name summary.md which a summary of every file here')
    perform_task("read the available files one at a time and output a final summary of the purpose of this project in summary.txt")