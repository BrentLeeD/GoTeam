import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import base64
import io
import csv
import json
import os
import pyperclip  # For clipboard functionality

# Page configuration
st.set_page_config(
    page_title="CoachMee Certificate Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, h4 {
        color: #2c3e50;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #009245;
        color: white;
    }
    .download-btn {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        text-decoration: none;
        border-radius: 4px;
        display: inline-flex;
        align-items: center;
        margin-right: 10px;
    }
    .whatsapp-btn {
        background-color: #25D366;
        color: white;
    }
    .email-btn {
        background-color: #0078D4;
        color: white;
    }
    .copy-btn {
        background-color: #6c757d;
        color: white;
    }
    .certificate-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #009245;
        margin: 20px 0;
    }
    .footer {
        margin-top: 2rem;
        text-align: center;
        border-top: 1px solid #eee;
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and intro
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #009245; margin-bottom: 0.5rem;">CoachMee Certificate Generator</h1>
    <p style="font-size: 1.2rem; color: #555;">Generate personalized completion letters for participants in the Make Your Own Money (MYOM) WhatsApp learning journey</p>
</div>
""", unsafe_allow_html=True)

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

# Initialize session state variables
if 'last_certificate_data' not in st.session_state:
    st.session_state.last_certificate_data = {
        'participant_data': None,
        'certificate_text': None
    }

if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = False

if 'template_name' not in st.session_state:
    st.session_state.template_name = "Default Template"

if 'prompt_template' not in st.session_state:
    st.session_state.prompt_template = DEFAULT_PROMPT_TEMPLATE

if 'system_instruction' not in st.session_state:
    st.session_state.system_instruction = SYSTEM_INSTRUCTION

# Function to generate certificate
def generate_certificate(participant_data, prompt_template=None, system_instruction=None):
    """Generate a personalized certificate using Google's Gemini model."""

    if prompt_template is None:
        prompt_template = st.session_state.prompt_template

    if system_instruction is None:
        system_instruction = st.session_state.system_instruction

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
        # Set up the model
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
            generation_config=generation_config
        )

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

# Function to create download links
def get_download_link(certificate_text, name):
    """Create download links for certificate."""
    # Text file
    b64 = base64.b64encode(certificate_text.encode()).decode()
    filename = f"certificate_{name.replace(' ', '_')}.txt"
    
    # Format for different platforms
    whatsapp_text = certificate_text.replace('\n', '%0A')  # Keep for compatibility
    email_subject = f"Certificate of Completion for {name}"
    email_body = certificate_text.replace('\n', '%0D%0A')
    
    return filename, b64, whatsapp_text, email_subject, email_body

# Function to add a copy to clipboard button that works with Streamlit
def add_copy_button(certificate_text):
    """Add a copy to clipboard button for the certificate text."""
    # Create a button for copying text
    if st.button("📋 Copy to Clipboard", key="copy_btn", use_container_width=True, 
                type="secondary"):
        try:
            # Try using pyperclip (works in most environments)
            import pyperclip
            pyperclip.copy(certificate_text)
            st.success("Certificate copied to clipboard!")
        except:
            # Fallback to displaying text that can be easily copied
            st.text_area("Copy this text manually:", value=certificate_text, 
                        height=100, label_visibility="collapsed")
            st.info("The text has been selected above. Use Ctrl+C (or Cmd+C on Mac) to copy.")
        
    return

# Create tabs
tab1, tab2, tab3 = st.tabs(["Generate Certificate", "Prompt Engineering", "Batch Processing"])

# Tab 1: Generate Certificate
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Participant Information")
        
        # Add a button to load sample data
        if st.button("Load Sample Data", key="load_sample"):
            sample = load_sample_data()
            st.session_state.name = sample["name"]
            st.session_state.gender = sample["gender"]
            st.session_state.completion_date = sample["completion_date"]
            st.session_state.strengths = sample["strengths"]
            st.session_state.goals = sample["goals"]
            st.session_state.myom_status = sample["myom_status"]
            st.session_state.learning_impact_option = "Custom response"
            st.session_state.custom_impact = sample["learning_impact"]
        
        # Name input
        name = st.text_input("Name", value=st.session_state.get("name", ""), 
                            placeholder="e.g., Thabo Mokoena")
        
        # Gender selection
        gender = st.selectbox("Gender", options=["Male", "Female", "Other"], 
                             index=0 if not st.session_state.get("gender") else 
                             ["Male", "Female", "Other"].index(st.session_state.get("gender")))
        
        # Date input
        completion_date = st.text_input("Completion Date", value=st.session_state.get("completion_date", ""), 
                                       placeholder="e.g., 15 March 2025")
        
        # Strengths input
        strengths = st.text_area("Strengths", value=st.session_state.get("strengths", ""), 
                               placeholder="e.g., Communication skills, adaptability, creative problem-solving", 
                               height=80)
        
        # Goals input
        goals = st.text_area("Goals", value=st.session_state.get("goals", ""), 
                           placeholder="e.g., Start a small business, save for education", 
                           height=80)
        
        # MYOM status
        myom_status_options = [
            "I've never thought about making money for myself – I just want a job or a chance to study",
            "I've thought about making money for myself, but I've never actually done so",
            "I have made money for myself before, but I don't do it all the time",
            "I'm making money for myself, and I want to keep making money and grow my business"
        ]
        
        myom_status = st.selectbox("MYOM Status", options=myom_status_options,
                                  index=0 if not st.session_state.get("myom_status") else
                                  myom_status_options.index(st.session_state.get("myom_status")))
        
        # Learning impact
        learning_impact_options = [
            "I learned a lot and am applying it daily",
            "I learned some useful things that I'm starting to apply",
            "I learned a few things that might be helpful",
            "I didn't learn much that was useful to me",
            "Custom response"
        ]
        
        learning_impact_option = st.selectbox("Learning Impact", options=learning_impact_options,
                                           index=0 if not st.session_state.get("learning_impact_option") else
                                           learning_impact_options.index(st.session_state.get("learning_impact_option")))
        
        # Custom impact input (shown conditionally)
        custom_impact = ""
        if learning_impact_option == "Custom response":
            custom_impact = st.text_area("Custom Learning Impact", 
                                       value=st.session_state.get("custom_impact", ""),
                                       placeholder="Enter custom learning impact here", 
                                       height=80)
    
    with col2:
        st.subheader("API Authentication")
        api_key = st.text_input("Google API Key", type="password", 
                              help="Enter your Google Gemini API key")
        
        if st.button("Set API Key"):
            if not api_key:
                st.error("Please enter an API key")
            else:
                try:
                    # Configure Gemini with the provided API key
                    genai.configure(api_key=api_key)
                    st.session_state.api_key_set = True
                    st.success("API key set successfully! You can now generate certificates.")
                except Exception as e:
                    st.error(f"Error setting API key: {str(e)}")
    
    # Buttons for generating certificates
    col1, col2 = st.columns(2)
    with col1:
        generate_button = st.button("Generate Certificate", 
                                  type="primary", 
                                  disabled=not st.session_state.api_key_set)
    with col2:
        regenerate_button = st.button("Regenerate Certificate", 
                                    disabled=not st.session_state.api_key_set or 
                                    st.session_state.last_certificate_data['participant_data'] is None)
    
    # Certificate generation logic
    if generate_button and st.session_state.api_key_set:
        if not name or not completion_date or not strengths or not goals:
            st.error("Please fill in all required fields (Name, Date, Strengths, and Goals)")
        else:
            with st.spinner("Generating certificate..."):
                # Determine the final learning impact text
                if learning_impact_option == "Custom response":
                    final_learning_impact = custom_impact
                else:
                    final_learning_impact = learning_impact_option
                
                # Create participant data
                participant_data = {
                    "name": name,
                    "gender": gender,
                    "completion_date": completion_date,
                    "strengths": strengths,
                    "goals": goals,
                    "myom_status": myom_status,
                    "learning_impact": final_learning_impact
                }
                
                # Generate certificate
                certificate_text = generate_certificate(participant_data)
                
                # Save for regeneration
                st.session_state.last_certificate_data['participant_data'] = participant_data
                st.session_state.last_certificate_data['certificate_text'] = certificate_text
                
                # Save form values to session state
                st.session_state.name = name
                st.session_state.gender = gender
                st.session_state.completion_date = completion_date
                st.session_state.strengths = strengths
                st.session_state.goals = goals
                st.session_state.myom_status = myom_status
                st.session_state.learning_impact_option = learning_impact_option
                st.session_state.custom_impact = custom_impact
                
                # Display certificate with better formatting and id for copy functionality
                st.subheader("Generated Certificate")
                # Replace newlines with <br> tags and wrap in div with id for copying
                formatted_certificate = certificate_text.replace('\n', '<br>')
                st.markdown(f'<div class="certificate-container" id="certificate-text">{formatted_certificate}</div>', unsafe_allow_html=True)
                
                # Create download links
                filename, b64, whatsapp_text, email_subject, email_body = get_download_link(certificate_text, name)
                
                # Add download and email buttons (WhatsApp removed as requested)
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 Download as Text",
                        data=certificate_text,
                        file_name=filename,
                        mime="text/plain",
                    )
                
                with col2:
                    st.markdown(
                        f'<a href="mailto:?subject={email_subject}&body={email_body}" class="stButton"><button style="background-color: #0078D4; color: white;">📧 Send via Email</button></a>',
                        unsafe_allow_html=True
                    )
                
                # Add a proper Streamlit copy button
                add_copy_button(certificate_text)
    
    # Regenerate certificate logic
    if regenerate_button and st.session_state.api_key_set:
        if st.session_state.last_certificate_data['participant_data'] is None:
            st.error("No previous certificate data found")
        else:
            with st.spinner("Regenerating certificate..."):
                # Generate a new certificate with the same data
                certificate_text = generate_certificate(st.session_state.last_certificate_data['participant_data'])
                
                # Update the stored certificate
                st.session_state.last_certificate_data['certificate_text'] = certificate_text
                
                # Display regenerated certificate with better formatting
                st.subheader("Regenerated Certificate")
                # Replace newlines with <br> tags and wrap in div with id for copying
                formatted_certificate = certificate_text.replace('\n', '<br>')
                st.markdown(f'<div class="certificate-container" id="certificate-text">{formatted_certificate}</div>', unsafe_allow_html=True)
                
                # Create download links
                name = st.session_state.last_certificate_data['participant_data']['name']
                filename, b64, whatsapp_text, email_subject, email_body = get_download_link(certificate_text, name)
                
                # Add download and email buttons (WhatsApp removed as requested)
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 Download as Text",
                        data=certificate_text,
                        file_name=filename,
                        mime="text/plain",
                    )
                
                with col2:
                    st.markdown(
                        f'<a href="mailto:?subject={email_subject}&body={email_body}" class="stButton"><button style="background-color: #0078D4; color: white;">📧 Send via Email</button></a>',
                        unsafe_allow_html=True
                    )
                
                # Add a proper Streamlit copy button
                add_copy_button(certificate_text)

# Tab 2: Prompt Engineering
with tab2:
    st.subheader("Customize Prompt Template and System Instructions")
    st.write("Customize the prompt template and system instructions used to generate certificates.")
    
    # Template name
    template_name = st.text_input("Template Name", value=st.session_state.template_name, 
                                placeholder="e.g., Business Focus")
    
    # System instructions
    st.markdown("### System Instructions")
    st.write("NOTE: For Gemini 2.0 we combine these with the prompt - they are not sent separately.")
    system_instruction = st.text_area("System Instructions", value=st.session_state.system_instruction, 
                                    height=200)
    
    # Prompt template
    st.markdown("### Prompt Template")
    st.write("This is the actual template that will be filled with participant data. Use {name}, {gender}, {completion_date}, etc. as placeholders.")
    prompt_template = st.text_area("Prompt Template", value=st.session_state.prompt_template, 
                                 height=300)
    
    # Save and load buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Prompt Template"):
            if not template_name or not prompt_template:
                st.error("Template name and content are required")
            else:
                # Save template to session state
                st.session_state.template_name = template_name
                st.session_state.prompt_template = prompt_template
                st.session_state.system_instruction = system_instruction
                
                # Create downloadable JSON
                prompt_data = {
                    "name": template_name,
                    "template": prompt_template,
                    "system_instruction": system_instruction
                }
                
                # Make JSON available for download
                json_data = json.dumps(prompt_data, indent=2)
                filename = f"prompt_template_{template_name.lower().replace(' ', '_')}.json"
                
                st.download_button(
                    label="📄 Download Template",
                    data=json_data,
                    file_name=filename,
                    mime="application/json",
                )
                
                st.success(f'Template "{template_name}" saved successfully!')
    
    with col2:
        uploaded_file = st.file_uploader("Upload Prompt Template", type=["json"])
        if uploaded_file is not None:
            try:
                # Read and parse the JSON file
                content = uploaded_file.read()
                prompt_data = json.loads(content)
                
                # Update session state with the loaded template
                st.session_state.template_name = prompt_data.get("name", "Custom Template") 
                st.session_state.prompt_template = prompt_data.get("template", DEFAULT_PROMPT_TEMPLATE)
                st.session_state.system_instruction = prompt_data.get("system_instruction", SYSTEM_INSTRUCTION)
                
                st.success(f"Template \"{prompt_data.get('name', 'Custom Template')}\" loaded successfully!")
                
                # Refresh the page to show updated values
                st.rerun()
            except Exception as e:
                st.error(f"Error loading template: {str(e)}")
    
    # Variables reference
    st.markdown("### Available Template Variables")
    st.markdown("""
    | Variable | Description | Example |
    | --- | --- | --- |
    | {name} | Participant's full name | Thabo Mokoena |
    | {gender} | Participant's gender | Male, Female, Other |
    | {completion_date} | When they completed 30 check-ins | 15 March 2025 |
    | {strengths} | Participant's self-identified strengths | Communication skills, adaptability |
    | {goals} | Participant's personal/professional goals | Start a small business selling crafts |
    | {myom_status} | Current relationship with self-employment | I have made money for myself before |
    | {learning_impact} | Self-reported impact of the program | I learned how to price my products |
    | {pronoun} | Appropriate pronoun based on gender | he, she, they |
    | {pronoun_cap} | Capitalized pronoun | He, She, They |
    """)

# Tab 3: Batch Processing
with tab3:
    st.subheader("Batch Certificate Generation")
    st.write("Upload a CSV file with participant data to generate multiple certificates at once.")
    
    # Upload CSV file
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    
    # Process batch if file is uploaded
    if uploaded_file is not None and st.session_state.api_key_set:
        # Read CSV
        csv_data = []
        try:
            csv_file = io.StringIO(uploaded_file.getvalue().decode('utf-8'))
            reader = csv.DictReader(csv_file)
            field_names = reader.fieldnames
            
            # Check for required fields
            required_fields = ['name', 'gender', 'completion_date', 'strengths', 'goals', 'myom_status', 'learning_impact']
            missing_fields = [field for field in required_fields if field not in field_names]
            
            if missing_fields:
                st.error(f"Missing required columns in CSV: {', '.join(missing_fields)}")
            else:
                # Read CSV data
                for row in reader:
                    csv_data.append(row)
                
                # Set up progress tracking
                total_rows = len(csv_data)
                st.info(f"Found {total_rows} participants in the CSV file. Ready to generate certificates.")
                
                if st.button("Generate Batch Certificates"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Process each row
                    all_certificates = []
                    errors = []
                    
                    for i, participant in enumerate(csv_data):
                        try:
                            status_text.info(f"Generating certificate {i+1}/{total_rows} for {participant.get('name', 'Unknown')}...")
                            
                            # Generate certificate
                            certificate = generate_certificate(participant)
                            
                            # Store certificate
                            all_certificates.append({
                                'name': participant.get('name', 'Unknown'),
                                'certificate': certificate
                            })
                            
                            # Update progress
                            progress_bar.progress((i + 1) / total_rows)
                        except Exception as e:
                            errors.append(f"Error processing row {i+1} ({participant.get('name', 'Unknown')}): {str(e)}")
                    
                    # Create combined text file with all certificates
                    combined_text = "\n\n" + "="*50 + "\n\n".join([f"CERTIFICATE FOR: {cert['name']}\n\n{cert['certificate']}" for cert in all_certificates])
                    
                    # Create CSV for download
                    result_rows = []
                    for cert in all_certificates:
                        result_rows.append({
                            "Name": cert['name'],
                            "Certificate": cert['certificate']
                        })
                    
                    result_df = pd.DataFrame(result_rows)
                    csv_data = result_df.to_csv(index=False)
                    
                    # Update status
                    if errors:
                        error_text = "\n".join(errors)
                        st.warning(f"Completed with {len(errors)} errors:\n{error_text}")
                    else:
                        st.success(f"Successfully generated {len(all_certificates)} certificates!")
                    
                    # Provide download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Download All as Text",
                            data=combined_text,
                            file_name="all_certificates.txt",
                            mime="text/plain",
                        )
                    
                    with col2:
                        st.download_button(
                            label="📊 Download Results as CSV",
                            data=csv_data,
                            file_name="all_certificates.csv",
                            mime="text/csv",
                        )
                    
                    # Show sample certificate
                    if all_certificates:
                        st.subheader("Sample Certificate")
                        st.write(f"**{all_certificates[0]['name']}**")
                        st.markdown(f'<div class="certificate-container">{all_certificates[0]["certificate"]}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error processing batch: {str(e)}")
    elif not st.session_state.api_key_set and uploaded_file is not None:
        st.error("Please set the API key in the Generate Certificate tab before processing batch certificates.")
    
    # Show CSV format example
    st.subheader("CSV Format Example:")
    csv_example = """name,gender,completion_date,strengths,goals,myom_status,learning_impact
Thabo Mokoena,Male,15 March 2025,"Communication skills, adaptability, creative problem-solving","Start a small business selling handcrafted items, save money for further education","I have made money for myself before, but I don't do it all the time","The program helped me understand how to price my products and manage my time between my job and side hustle"
Nomsa Dlamini,Female,16 March 2025,"Organization, attention to detail, team coordination","Find employment in administration, start a small catering business on weekends","I've thought about making money for myself, but I've never actually done so","I learned some useful things that I'm starting to apply"
"""
    
    st.code(csv_example, language="text")

# Footer
st.markdown("""
<div class="footer">
    <p>CoachMee Certificate Generator v1.0 | Harambee Youth Employment Accelerator | © 2025</p>
</div>
""", unsafe_allow_html=True)
