# Install required packages
!pip install google-generativeai pandas ipywidgets google-auth google-auth-oauthlib google-auth-httplib2

# Import required libraries
import pandas as pd
import google.generativeai as genai
import ipywidgets as widgets
from IPython.display import display, HTML, Javascript
from datetime import datetime
import base64
import os
import time
import json
import io
import csv
from google.colab import files

# Manual API key input
api_key_input = widgets.Password(
    description='API Key:',
    placeholder='Enter your Google API key',
    layout=widgets.Layout(width='50%')
)

api_key_button = widgets.Button(
    description='Set API Key',
    button_style='primary',
    layout=widgets.Layout(width='20%')
)

api_key_status = widgets.HTML("")

# Function to set API key
def set_api_key(b):
    key = api_key_input.value
    if not key:
        api_key_status.value = '<div style="color: red; padding: 10px;">Please enter an API key</div>'
        return

    try:
        # Configure Gemini with the provided API key
        genai.configure(api_key=key)
        api_key_status.value = '<div style="color: green; padding: 10px;">API key set successfully! You can now generate certificates.</div>'
    except Exception as e:
        api_key_status.value = f'<div style="color: red; padding: 10px;">Error setting API key: {str(e)}</div>'

api_key_button.on_click(set_api_key)

display(widgets.HTML("<h2>Google API Authentication</h2>"))
display(widgets.HTML("<p>Enter your Google API key to use the Gemini API:</p>"))
display(widgets.HBox([api_key_input, api_key_button]))
display(api_key_status)



# Prompt Templates with System Instructions
DEFAULT_PROMPT_TEMPLATE = """
Create a short, personalized letter of completion for a participant in the "Make Your Own Money" (MYOM) WhatsApp learning journey delivered through CoachMee. This program is part of the National Youth Service (NYS) in South Africa.

Here is the participant information:
- Name: {name}
- Gender: {gender}
- Completion Date: {completion_date}
- Strengths (identified by participant): {strengths}
- Goals (identified by participant): {goals}
- MYOM Status After Program: {myom_status}
- Learning Impact (participant feedback): {learning_impact}

Follow this specific format and style for the letter - it must be ONE PARAGRAPH ONLY, similar in length to this example:

"On 20 September 2024, Zikhona Mandende completed 30 goal-setting conversations with 'Coachmee' - a smart chatbot powered by SAYouth.mobi. In her first goal-setting session with Coachmee, she introduced herself as a lovely person who enjoys smiling and has good interpersonal, problem-solving, basic computer, and communication skills. She expressed her desire to gain more skills to advance her career in the contact center industry, aiming to become a manager. The 30 Whatsapp-enabled sessions that followed focused on the importance of setting daily goals to achieve long-term objectives and aspirations. Zikhona also embraced meditation and journaling, which have been proven to help manage emotions and improve well-being. Coachmee says it was a pleasure coaching Zikhona - he learned a lot from her, and wishes her all the best in her future endeavors!"

Your letter should follow this format:

"On {completion_date}, {name} completed 30 income-generating skills conversations with 'CoachMee' - a smart chatbot powered by SAYouth.mobi. In {pronoun}r first session with CoachMee, {pronoun} introduced {pronoun}mself as someone with strengths in [mention 2-3 strengths from the participant data]. {pronoun_cap} expressed {pronoun}r desire to [mention their primary goal]. The 30 WhatsApp-enabled sessions that followed focused on essential skills for making your own money, including [mention 1-2 MYOM topics like spotting opportunities, finding funding, marketing, etc.]. {name} engaged with inspiring stories from young South African entrepreneurs like Octoria's sneaker cleaning business and Thato's spaza shop success. {pronoun_cap} also embraced tools for goal-setting and planning, which have been proven to help develop the entrepreneurial mindset needed for success. CoachMee says it was a pleasure coaching {name} - {pronoun} showed dedication by completing all 30 sessions, and SA Youth wishes {pronoun}m continued success on {pronoun}r journey to make {pronoun}r own money!"

Make it exactly ONE PARAGRAPH with South African references, warm and encouraging. It should be similar in length to the example with Zikhona.
"""

SYSTEM_INSTRUCTION = """
You are an expert certificate writer for the CoachMee program at Harambee Youth Employment Accelerator in South Africa.
Your task is to create personalized, warm, and authentic completion certificates that highlight the participant's journey through the Make Your Own Money (MYOM) WhatsApp learning program.

Follow these principles:
1. Use a warm, conversational South African tone - as if sending a WhatsApp message to a friend
2. Incorporate specific South African entrepreneurial references (spaza shops, amagwinya businesses, etc.)
3. Reference real MYOM content like Octoria's sneaker cleaning business, Thato's spaza shop, and Nomsa's funding journey
4. Highlight the participant's strengths and goals in a meaningful way
5. Keep the certificate to exactly ONE paragraph of appropriate length
6. Use proper pronouns based on the participant's gender
7. Make the certificate something the participant would be proud to share with friends, family and potential employers

Focus on the entrepreneurial skills and mindset developed through the program, emphasizing how the participant can use these skills to make their own money.
"""

# Save and load prompt templates
def save_prompt_template(name, template, system_instruction):
    """Save a prompt template to a JSON file."""
    prompt_data = {
        "name": name,
        "template": template,
        "system_instruction": system_instruction
    }

    # Encode to base64 for download
    prompt_json = json.dumps(prompt_data, indent=2)
    b64 = base64.b64encode(prompt_json.encode()).decode()
    filename = f"prompt_template_{name.lower().replace(' ', '_')}.json"

    # Create download link
    href = f'<a download="{filename}" href="data:application/json;base64,{b64}">Download Prompt Template</a>'
    display(HTML(href))

    return prompt_data

def load_prompt_template_from_file():
    """Load a prompt template from an uploaded JSON file."""
    uploaded = files.upload()

    if not uploaded:
        return None, None, "No file selected"

    try:
        file_name = list(uploaded.keys())[0]
        content = uploaded[file_name]
        prompt_data = json.loads(content)

        return prompt_data.get("name", "Custom Template"), prompt_data.get("template", ""), prompt_data.get("system_instruction", "")
    except Exception as e:
        return None, None, f"Error loading template: {str(e)}"

# Function to generate certificate
def generate_certificate(participant_data, prompt_template=None, system_instruction=None):
    """Generate a personalized certificate using Google's Gemini model."""

    if prompt_template is None:
        prompt_template = DEFAULT_PROMPT_TEMPLATE

    if system_instruction is None:
        system_instruction = SYSTEM_INSTRUCTION

    # Get proper pronoun based on gender
    pronoun = "he"
    if participant_data.get('gender', '').lower() == "female":
        pronoun = "she"
    elif participant_data.get('gender', '').lower() == "other":
        pronoun = "they"

    pronoun_cap = pronoun.capitalize()

    # Format the prompt template with participant data
    formatted_prompt = prompt_template.format(
        name=participant_data['name'],
        gender=participant_data.get('gender', 'Male'),
        completion_date=participant_data['completion_date'],
        strengths=participant_data['strengths'],
        goals=participant_data['goals'],
        myom_status=participant_data['myom_status'],
        learning_impact=participant_data['learning_impact'],
        pronoun=pronoun,
        pronoun_cap=pronoun_cap
    )

    try:
        # Set up the model - Check if "gemini-2.0-pro-exp-02-05" is available
        model = genai.GenerativeModel("gemini-2.0-flash-001")

        # Generate content with system instruction AND formatted prompt
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2024,
        }

        # Create a properly formatted prompt that includes system instruction
        full_prompt = f"{system_instruction}\n\n{formatted_prompt}"



        # Generate content
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config        )

        # Check if we have any candidates
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            return "Error: No response generated. The model may have rejected the content. Try adjusting your prompt."

        # Directly access text to avoid the empty candidates issue
        return response.candidates[0].content.parts[0].text
    except Exception as e:
        return f"Error generating certificate: {str(e)}"

# Sample data for demonstration
def load_sample_data():
    """Load sample data for demonstration purposes."""
    return {
        "name": "Thabo Mokoena",
        "gender": "Male",
        "completion_date": "15 March 2025",
        "strengths": "Communication skills, adaptability, creative problem-solving",
        "goals": "Start a small business selling handcrafted items, save money for further education",
        "myom_status": "I have made money for myself before, but I don't do it all the time",
        "learning_impact": "The program helped me understand how to price my products and manage my time between my job and side hustle"
    }

# Create prompt engineering interface
def create_prompt_engineering_interface():
    # Create output for this section
    prompt_output = widgets.Output()

    with prompt_output:
        # Prompt template editor
        template_name_widget = widgets.Text(
            description='Template Name:',
            placeholder='e.g., Business Focus',
            value='Default Template',
            layout=widgets.Layout(width='80%')
        )

        prompt_template_widget = widgets.Textarea(
            placeholder='Enter prompt template here...',
            value=DEFAULT_PROMPT_TEMPLATE,
            layout=widgets.Layout(width='100%', height='300px')
        )

        system_instruction_widget = widgets.Textarea(
            placeholder='Enter system instructions here...',
            value=SYSTEM_INSTRUCTION,
            layout=widgets.Layout(width='100%', height='200px')
        )

        # Buttons for saving/loading templates
        save_button = widgets.Button(
            description='Save Prompt Template',
            button_style='primary',
            layout=widgets.Layout(width='50%')
        )

        load_button = widgets.Button(
            description='Load Prompt Template',
            button_style='info',
            layout=widgets.Layout(width='50%')
        )

        template_status = widgets.HTML("")

        def on_save_button_clicked(b):
            name = template_name_widget.value
            template = prompt_template_widget.value
            instruction = system_instruction_widget.value

            if not name or not template:
                template_status.value = '<div style="color: red; padding: 10px; border-left: 5px solid red;">Template name and content are required</div>'
                return

            save_prompt_template(name, template, instruction)
            template_status.value = f'<div style="color: green; padding: 10px; border-left: 5px solid green;">Template "{name}" saved successfully! You can download it using the link above.</div>'

        def on_load_button_clicked(b):
            name, template, instruction = load_prompt_template_from_file()

            if name and template:
                template_name_widget.value = name
                prompt_template_widget.value = template
                if instruction:
                    system_instruction_widget.value = instruction

                template_status.value = f'<div style="color: green; padding: 10px; border-left: 5px solid green;">Template "{name}" loaded successfully!</div>'
            else:
                template_status.value = f'<div style="color: red; padding: 10px; border-left: 5px solid red;">{instruction}</div>'

        save_button.on_click(on_save_button_clicked)
        load_button.on_click(on_load_button_clicked)

        # Display prompt engineering widgets
        display(widgets.HTML("<h2>Prompt Engineering</h2>"))
        display(widgets.HTML("<p>Customize the prompt template and system instructions used to generate certificates.</p>"))

        display(widgets.HTML("<h3>Template Name</h3>"))
        display(template_name_widget)

        display(widgets.HTML("<h3>System Instructions</h3>"))
        display(widgets.HTML("<p>NOTE: For Gemini 2.0 we combine these with the prompt - they are not sent separately.</p>"))
        display(system_instruction_widget)

        display(widgets.HTML("<h3>Prompt Template</h3>"))
        display(widgets.HTML("<p>This is the actual template that will be filled with participant data. Use {name}, {gender}, {completion_date}, etc. as placeholders.</p>"))
        display(prompt_template_widget)

        display(widgets.HBox([save_button, load_button]))
        display(template_status)

        # Template variables reference
        display(widgets.HTML("<h3>Available Template Variables</h3>"))
        variables_table = """
        <table style="width:100%; border-collapse: collapse;">
          <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Variable</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Description</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Example</th>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{name}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Participant's full name</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Thabo Mokoena</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{gender}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Participant's gender</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Male, Female, Other</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{completion_date}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">When they completed 30 check-ins</td>
            <td style="border: 1px solid #ddd; padding: 8px;">15 March 2025</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{strengths}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Participant's self-identified strengths</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Communication skills, adaptability</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{goals}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Participant's personal/professional goals</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Start a small business selling crafts</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{myom_status}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Current relationship with self-employment</td>
            <td style="border: 1px solid #ddd; padding: 8px;">I have made money for myself before</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{learning_impact}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Self-reported impact of the program</td>
            <td style="border: 1px solid #ddd; padding: 8px;">I learned how to price my products</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{pronoun}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Appropriate pronoun based on gender</td>
            <td style="border: 1px solid #ddd; padding: 8px;">he, she, they</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{pronoun_cap}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">Capitalized pronoun</td>
            <td style="border: 1px solid #ddd; padding: 8px;">He, She, They</td>
          </tr>
        </table>
        """
        display(HTML(variables_table))

    return prompt_output, template_name_widget, prompt_template_widget, system_instruction_widget

# Create the main certificate form
def create_certificate_form(template_name_widget, prompt_template_widget, system_instruction_widget):
    # Create widgets
    name_widget = widgets.Text(
        description='Name:',
        placeholder='e.g., Thabo Mokoena',
        layout=widgets.Layout(width='80%')
    )

    gender_widget = widgets.Dropdown(
        options=['Male', 'Female', 'Other'],
        value='Male',
        description='Gender:',
        layout=widgets.Layout(width='50%')
    )

    date_widget = widgets.DatePicker(
        description='Completion Date:',
        layout=widgets.Layout(width='50%')
    )

    strengths_widget = widgets.Textarea(
        description='Strengths:',
        placeholder='e.g., Communication skills, adaptability, creative problem-solving',
        layout=widgets.Layout(width='80%', height='80px')
    )

    goals_widget = widgets.Textarea(
        description='Goals:',
        placeholder='e.g., Start a small business, save for education',
        layout=widgets.Layout(width='80%', height='80px')
    )

    myom_status_options = [
        "I've never thought about making money for myself – I just want a job or a chance to study",
        "I've thought about making money for myself, but I've never actually done so",
        "I have made money for myself before, but I don't do it all the time",
        "I'm making money for myself, and I want to keep making money and grow my business"
    ]

    myom_status_widget = widgets.Dropdown(
        options=myom_status_options,
        value=myom_status_options[0],
        description='MYOM Status:',
        layout=widgets.Layout(width='80%')
    )

    learning_impact_options = [
        "I learned a lot and am applying it daily",
        "I learned some useful things that I'm starting to apply",
        "I learned a few things that might be helpful",
        "I didn't learn much that was useful to me",
        "Custom response"
    ]

    learning_impact_widget = widgets.Dropdown(
        options=learning_impact_options,
        value=learning_impact_options[0],
        description='Learning Impact:',
        layout=widgets.Layout(width='80%')
    )

    custom_impact_widget = widgets.Textarea(
        placeholder='Enter custom learning impact here',
        layout=widgets.Layout(width='80%', height='80px')
    )

    button = widgets.Button(
        description='Generate Certificate',
        button_style='success',
        layout=widgets.Layout(width='50%')
    )

    regenerate_button = widgets.Button(
        description='Regenerate Certificate',
        button_style='warning',
        layout=widgets.Layout(width='50%'),
        disabled=True
    )

    output = widgets.Output()

    # Load sample data button
    load_sample_button = widgets.Button(
        description='Load Sample Data',
        button_style='info',
        layout=widgets.Layout(width='50%')
    )

    def on_load_sample_button_clicked(b):
        sample_data = load_sample_data()
        name_widget.value = sample_data['name']
        gender_widget.value = sample_data['gender']
        # Convert string date to datetime for the date picker
        date_widget.value = datetime.strptime(sample_data['completion_date'], "%d %B %Y").date()
        strengths_widget.value = sample_data['strengths']
        goals_widget.value = sample_data['goals']
        myom_status_widget.value = sample_data['myom_status']
        learning_impact_widget.value = "Custom response"
        custom_impact_widget.value = sample_data['learning_impact']

    load_sample_button.on_click(on_load_sample_button_clicked)

    def on_learning_impact_change(change):
        if change['new'] == "Custom response":
            custom_impact_widget.layout.display = ''
        else:
            custom_impact_widget.layout.display = 'none'

    learning_impact_widget.observe(on_learning_impact_change, names='value')

    # Initially hide the custom impact field
    custom_impact_widget.layout.display = 'none'

    # Keep track of the last generated certificate data
    last_certificate_data = {
        'participant_data': None,
        'certificate_text': None
    }

    def generate_certificate_from_form():
        # Format the date
        completion_date = date_widget.value.strftime("%d %B %Y")

        # Get the correct learning impact text
        if learning_impact_widget.value == "Custom response":
            final_learning_impact = custom_impact_widget.value
        else:
            final_learning_impact = learning_impact_widget.value

        # Create participant data
        participant_data = {
            "name": name_widget.value,
            "gender": gender_widget.value,
            "completion_date": completion_date,
            "strengths": strengths_widget.value,
            "goals": goals_widget.value,
            "myom_status": myom_status_widget.value,
            "learning_impact": final_learning_impact
        }

        # Get the prompt template and system instruction
        template = prompt_template_widget.value
        system = system_instruction_widget.value

        # Generate certificate
        certificate_text = generate_certificate(
            participant_data,
            prompt_template=template,
            system_instruction=system
        )

        # Save for possible regeneration
        last_certificate_data['participant_data'] = participant_data
        last_certificate_data['certificate_text'] = certificate_text

        return certificate_text

    def on_button_clicked(b):
        with output:
            output.clear_output()
            print("Generating certificate... Please wait.")

            if not name_widget.value or not date_widget.value or not strengths_widget.value or not goals_widget.value:
                print("Error: Please fill in all required fields (Name, Date, Strengths, and Goals)")
                return

            certificate_text = generate_certificate_from_form()

            # Display the certificate
            print("\n----- Generated Certificate -----\n")
            print(certificate_text)
            print("\n---------------------------------\n")

            # Create various download options
            # Text file
            text_b64 = base64.b64encode(certificate_text.encode()).decode()
            text_filename = f"certificate_{name_widget.value.replace(' ', '_')}.txt"
            text_href = f'<a download="{text_filename}" href="data:text/plain;base64,{text_b64}" class="download-link">Download as Text</a>'

            # WhatsApp-ready format
            whatsapp_text = certificate_text.replace('\n', '%0A')
            whatsapp_href = f'<a href="https://wa.me/?text={whatsapp_text}" target="_blank" class="whatsapp-link">Open in WhatsApp</a>'

            # Email-ready format
            email_subject = f"Certificate of Completion for {name_widget.value}"
            email_body = certificate_text.replace('\n', '%0D%0A')
            email_href = f'<a href="mailto:?subject={email_subject}&body={email_body}" class="email-link">Send via Email</a>'

            # Create fancy download links
            fancy_links = f"""
            <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
                <a download="{text_filename}" href="data:text/plain;base64,{text_b64}"
                   style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📄</span> Download as Text
                </a>

                <a href="https://wa.me/?text={whatsapp_text}" target="_blank"
                   style="background-color: #25D366; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📱</span> Open in WhatsApp
                </a>

                <a href="mailto:?subject={email_subject}&body={email_body}"
                   style="background-color: #0078D4; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📧</span> Send via Email
                </a>

                <button onclick="navigator.clipboard.writeText(`{certificate_text}`); alert('Certificate copied to clipboard!');"
                        style="background-color: #6c757d; color: white; padding: 10px 15px; border: none;
                               border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📋</span> Copy to Clipboard
                </button>
            </div>
            """

            display(HTML(fancy_links))

            # Enable regenerate button
            regenerate_button.disabled = False

    def on_regenerate_button_clicked(b):
        with output:
            output.clear_output()
            print("Regenerating certificate with the same data but potentially different wording...")

            if last_certificate_data['participant_data'] is None:
                print("Error: No previous certificate data found")
                return

            # Get the prompt template and system instruction
            template = prompt_template_widget.value
            system = system_instruction_widget.value

            # Generate a new certificate with the same data
            certificate_text = generate_certificate(
                last_certificate_data['participant_data'],
                prompt_template=template,
                system_instruction=system
            )

            # Update the stored certificate
            last_certificate_data['certificate_text'] = certificate_text

            # Display the certificate
            print("\n----- Regenerated Certificate -----\n")
            print(certificate_text)
            print("\n---------------------------------\n")

            # Create text file download link
            text_b64 = base64.b64encode(certificate_text.encode()).decode()
            name = last_certificate_data['participant_data']['name']
            text_filename = f"certificate_{name.replace(' ', '_')}_regenerated.txt"

            # WhatsApp-ready format
            whatsapp_text = certificate_text.replace('\n', '%0A')

            # Email-ready format
            email_subject = f"Certificate of Completion for {name}"
            email_body = certificate_text.replace('\n', '%0D%0A')

            # Create fancy download links (same as above)
            fancy_links = f"""
            <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
                <a download="{text_filename}" href="data:text/plain;base64,{text_b64}"
                   style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📄</span> Download as Text
                </a>

                <a href="https://wa.me/?text={whatsapp_text}" target="_blank"
                   style="background-color: #25D366; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📱</span> Open in WhatsApp
                </a>

                <a href="mailto:?subject={email_subject}&body={email_body}"
                   style="background-color: #0078D4; color: white; padding: 10px 15px; text-decoration: none;
                          border-radius: 4px; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📧</span> Send via Email
                </a>

                <button onclick="navigator.clipboard.writeText(`{certificate_text}`); alert('Certificate copied to clipboard!');"
                        style="background-color: #6c757d; color: white; padding: 10px 15px; border: none;
                               border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center;">
                   <span style="margin-right: 5px;">📋</span> Copy to Clipboard
                </button>
            </div>
            """

            display(HTML(fancy_links))

    button.on_click(on_button_clicked)
    regenerate_button.on_click(on_regenerate_button_clicked)

    # Create form output
    form_output = widgets.Output()

    with form_output:
        # Display widgets
        display(widgets.HTML("<h2>Certificate Generator</h2>"))
        display(widgets.HTML("<p>Enter participant information to generate a personalized certificate.</p>"))
        display(load_sample_button)
        display(widgets.HTML("<h3>Participant Information</h3>"))
        display(name_widget)
        display(gender_widget)
        display(date_widget)
        display(strengths_widget)
        display(goals_widget)
        display(myom_status_widget)
        display(learning_impact_widget)
        display(custom_impact_widget)
        display(widgets.HBox([button, regenerate_button]))
        display(output)

    return form_output

# Create batch processing interface
def create_batch_processing_interface(template_name_widget, prompt_template_widget, system_instruction_widget):
    batch_output = widgets.Output()

    with batch_output:
        display(widgets.HTML("<h2>Batch Certificate Generation</h2>"))
        display(widgets.HTML("<p>Upload a CSV file with participant data to generate multiple certificates at once.</p>"))

        upload_button = widgets.Button(
            description='Upload CSV File',
            button_style='primary',
            layout=widgets.Layout(width='50%')
        )

        batch_progress = widgets.IntProgress(
            value=0,
            min=0,
            max=100,
            description='Progress:',
            bar_style='info',
            style={'bar_color': '#2196F3'},
            orientation='horizontal'
        )

        batch_status = widgets.HTML("")
        batch_results = widgets.Output()

        def on_upload_button_clicked(b):
            with batch_results:
                batch_results.clear_output()
                batch_progress.value = 0
                batch_status.value = '<div style="padding: 10px; background-color: #f8f9fa; border-left: 5px solid #2196F3;">Please select a CSV file to upload...</div>'

                try:
                    uploaded = files.upload()

                    if not uploaded:
                        batch_status.value = '<div style="padding: 10px; background-color: #fff3cd; border-left: 5px solid #ffc107;">No file selected. Please try again.</div>'
                        return

                    file_name = list(uploaded.keys())[0]
                    content = uploaded[file_name]

                    # Parse CSV
                    csv_data = []
                    csv_file = io.StringIO(content.decode('utf-8'))
                    reader = csv.DictReader(csv_file)
                    field_names = reader.fieldnames

                    required_fields = ['name', 'gender', 'completion_date', 'strengths', 'goals', 'myom_status', 'learning_impact']
                    missing_fields = [field for field in required_fields if field not in field_names]

                    if missing_fields:
                        batch_status.value = f'<div style="padding: 10px; background-color: #f8d7da; border-left: 5px solid #dc3545;">Error: Missing required columns in CSV: {", ".join(missing_fields)}</div>'
                        return

                    # First pass to count rows
                    csv_file.seek(0)
                    next(reader)  # Skip header
                    for row in reader:
                        csv_data.append(row)

                    total_rows = len(csv_data)
                    batch_status.value = f'<div style="padding: 10px; background-color: #d1ecf1; border-left: 5px solid #17a2b8;">Processing {total_rows} certificates...</div>'
                    batch_progress.max = total_rows

                    # Get prompt template and system instruction
                    template = prompt_template_widget.value
                    system = system_instruction_widget.value

                    # Process each row
                    all_certificates = []
                    errors = []

                    for i, participant in enumerate(csv_data):
                        try:
                            # Generate certificate
                            certificate = generate_certificate(participant, prompt_template=template, system_instruction=system)

                            # Store certificate
                            all_certificates.append({
                                'name': participant.get('name', 'Unknown'),
                                'certificate': certificate
                            })

                            # Update progress
                            batch_progress.value = i + 1
                            batch_status.value = f'<div style="padding: 10px; background-color: #d1ecf1; border-left: 5px solid #17a2b8;">Generating certificate {i+1}/{total_rows} for {participant.get("name", "Unknown")}...</div>'
                        except Exception as e:
                            errors.append(f"Error processing row {i+1} ({participant.get('name', 'Unknown')}): {str(e)}")

                    # Create combined text file with all certificates
                    combined_text = "\n\n" + "="*50 + "\n\n".join([f"CERTIFICATE FOR: {cert['name']}\n\n{cert['certificate']}" for cert in all_certificates])

                    # Create download link
                    b64 = base64.b64encode(combined_text.encode()).decode()
                    filename = "all_certificates.txt"

                    # Create Excel/CSV outputs
                    result_rows = []
                    for cert in all_certificates:
                        result_rows.append({
                            "Name": cert['name'],
                            "Certificate": cert['certificate']
                        })

                    result_df = pd.DataFrame(result_rows)

                    # CSV download
                    csv_data = result_df.to_csv(index=False)
                    csv_b64 = base64.b64encode(csv_data.encode()).decode()

                    # Update status
                    if errors:
                        error_text = "<br>".join(errors)
                        batch_status.value = f'<div style="padding: 10px; background-color: #fff3cd; border-left: 5px solid #ffc107;">Completed with {len(errors)} errors:<br>{error_text}</div>'
                    else:
                        batch_status.value = f'<div style="padding: 10px; background-color: #d4edda; border-left: 5px solid #28a745;">Successfully generated {len(all_certificates)} certificates!</div>'

                    # Display download links
                    download_links = f"""
                    <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
                        <a download="all_certificates.txt" href="data:text/plain;base64,{b64}"
                           style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none;
                                  border-radius: 4px; display: inline-flex; align-items: center;">
                           <span style="margin-right: 5px;">📄</span> Download All as Text
                        </a>

                        <a download="all_certificates.csv" href="data:text/csv;base64,{csv_b64}"
                           style="background-color: #FFC107; color: white; padding: 10px 15px; text-decoration: none;
                                  border-radius: 4px; display: inline-flex; align-items: center;">
                           <span style="margin-right: 5px;">📊</span> Download Results as CSV
                        </a>
                    </div>
                    """

                    display(HTML(download_links))

                    # Show sample certificates
                    if all_certificates:
                        display(widgets.HTML("<h3>Sample Certificate</h3>"))
                        display(widgets.HTML(f"<p><strong>{all_certificates[0]['name']}</strong></p>"))
                        display(widgets.HTML(f"<p style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: Arial;'>{all_certificates[0]['certificate'].replace(chr(10), '<br>')}</p>"))

                except Exception as e:
                    batch_status.value = f'<div style="padding: 10px; background-color: #f8d7da; border-left: 5px solid #dc3545;">Error processing batch: {str(e)}</div>'

        upload_button.on_click(on_upload_button_clicked)

        # Display batch processing UI
        display(upload_button)
        display(batch_progress)
        display(batch_status)
        display(batch_results)

        # Show CSV format example
        csv_example = """name,gender,completion_date,strengths,goals,myom_status,learning_impact
Thabo Mokoena,Male,15 March 2025,"Communication skills, adaptability, creative problem-solving","Start a small business selling handcrafted items, save money for further education","I have made money for myself before, but I don't do it all the time","The program helped me understand how to price my products and manage my time between my job and side hustle"
Nomsa Dlamini,Female,16 March 2025,"Organization, attention to detail, team coordination","Find employment in administration, start a small catering business on weekends","I've thought about making money for myself, but I've never actually done so","I learned some useful things that I'm starting to apply"
"""

        display(widgets.HTML("<h3>CSV Format Example:</h3>"))
        display(widgets.HTML(f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre; overflow-x: auto;">
        {csv_example}
        </div>
        """))

    return batch_output

# Main application assembly
def main():
    # Add styling
    display(HTML("""
    <style>
        .tab-content {
            padding: 20px;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 .25rem .25rem;
        }
        h1, h2, h3, h4 {
            color: #2c3e50;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .widget-label {
            min-width: 150px;
        }
        .jupyter-widgets-output-area .output_subarea {
            max-width: 100%;
        }
    </style>
    """))

    # Title and intro
    display(HTML("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #009245; margin-bottom: 0.5rem;">CoachMee Certificate Generator</h1>
        <p style="font-size: 1.2rem; color: #555;">Generate personalized completion letters for participants in the Make Your Own Money (MYOM) WhatsApp learning journey</p>
    </div>
    """))

    # Create prompt engineering interface
    prompt_interface, template_name_widget, prompt_template_widget, system_instruction_widget = create_prompt_engineering_interface()

    # Create certificate form
    form_interface = create_certificate_form(template_name_widget, prompt_template_widget, system_instruction_widget)

    # Create batch processing interface
    batch_interface = create_batch_processing_interface(template_name_widget, prompt_template_widget, system_instruction_widget)

    # Create tabs
    tab = widgets.Tab(children=[form_interface, prompt_interface, batch_interface])
    tab.set_title(0, 'Generate Certificate')
    tab.set_title(1, 'Prompt Engineering')
    tab.set_title(2, 'Batch Processing')

    display(tab)

    # Footer
    display(HTML("""
    <div style="margin-top: 2rem; text-align: center; border-top: 1px solid #eee; padding-top: 1rem;">
        <p>CoachMee Certificate Generator v1.0 | Harambee Youth Employment Accelerator | © 2025</p>
    </div>
    """))

# Run the application
main()
