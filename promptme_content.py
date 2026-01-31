import streamlit as st
import json
import pandas as pd
import csv
import os
import io
import base64
from datetime import datetime
import re
import google.generativeai as genai
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="PromptMe - Content Edition",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling (entire CSS from previous implementation)
st.markdown("""
<style>
    /* CSS Styles - Same as in the previous implementation */
    .main .block-container {
        padding-top: 2rem;
    }
    /* ... (rest of the CSS from the previous artifact) ... */
</style>
""", unsafe_allow_html=True)

# Default templates optimized for Gemini 1.5 Flash
default_templates = {
    "Lifehack": """You're creating content for WhatsApp messages aimed at South African youth. 
    
Create a practical, concise lifehack related to {theme} in a {tone} tone.

Requirements:
- Length: {length} (about {word_count} words)
- Purpose: Help solve a common problem or improve daily life
- Style: Actionable with clear, numbered steps
- Format: Perfect for WhatsApp sharing (emoji-friendly)
{sa_context_prompt}

Make it compelling with an attention-grabbing opening and memorable conclusion.
""",
    "Nudge": """You're creating content for WhatsApp messages aimed at South African youth.

Generate a short, effective motivational nudge about {theme} in a {tone} tone.

Requirements:
- Length: {length} (about {word_count} words)
- Purpose: Gently encourage positive action
- Style: Conversational, direct, with a question to prompt reflection
- Format: Perfect for WhatsApp sharing
- Must include 1-2 relevant emojis
{sa_context_prompt}

Focus on building agency and hope, with a clear call to small, achievable action.
""",
    "Goal-Setting Advice": """You're creating content for WhatsApp messages aimed at South African youth.

Create practical goal-setting advice related to {theme} in a {tone} tone.

Requirements:
- Length: {length} (about {word_count} words)
- Purpose: Help people set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Style: Clear, structured, with numbered points
- Format: Perfect for WhatsApp sharing
{sa_context_prompt}

Include at least one concrete example of a good goal and how to break it down into smaller steps.
""",
    "Motivation": """You're creating content for WhatsApp messages aimed at South African youth.

Write a powerful motivational message about {theme} in a {tone} tone.

Requirements:
- Length: {length} (about {word_count} words)
- Purpose: Inspire action and build confidence
- Style: Energetic, positive, with practical wisdom
- Format: Perfect for WhatsApp sharing (emoji-friendly)
{sa_context_prompt}

Focus on overcoming challenges common to young South Africans, with an emphasis on resilience and personal agency.
""",
    "Quote": """You're creating content for WhatsApp messages aimed at South African youth.

Create a memorable, shareable quote about {theme} in a {tone} tone.

Requirements:
- Length: {length} (about {word_count} words)
- Purpose: Capture wisdom in a concise, impactful way
- Style: Memorable, with a strong rhythm or cadence
- Format: Perfect for social media sharing
{sa_context_prompt}

The quote should be attributed to "PromptMe Content Edition" and feel both fresh and timeless, avoiding clichés.
"""
}

# Main function to initialize the Streamlit app
def main():
    # Initialize session state variables
    initialize_session_state()

    # Title and introduction
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #009245; margin-bottom: 0.5rem;">PromptMe - Content Edition</h1>
        <p style="font-size: 1.2rem; color: #555;">Generate ideas for lifehacks, nudges, goal-setting advice, motivations, and quotes</p>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Generate Content", "Content Bank", "Batch Processing", "Settings"])

    # Implement tab contents using the previously developed functions
    with tab1:
        generate_content_tab()
    
    with tab2:
        content_bank_tab()
    
    with tab3:
        batch_processing_tab()
    
    with tab4:
        settings_tab()

def initialize_session_state():
    """Initialize all session state variables."""
    # API and generation settings
    if 'api_key_set' not in st.session_state:
        env_api_key = os.getenv("GOOGLE_API_KEY", "")
        if env_api_key:
            st.session_state.api_key = env_api_key
            st.session_state.api_key_set = True
        else:
            st.session_state.api_key_set = False

    # Content management
    if 'content_bank' not in st.session_state:
        st.session_state.content_bank = []

    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = ""

    if 'selected_themes' not in st.session_state:
        st.session_state.selected_themes = []

    # Themes bank
    if 'themes_bank' not in st.session_state:
        st.session_state.themes_bank = [
            "Growth Mindset", "Opportunity Awareness", "Career Development", 
            "Skill Building", "Financial Literacy", "Self-Employment", 
            "Entrepreneurship", "Networking", "Job Hunting", "Interview Preparation",
            "CV Writing", "Personal Branding", "Work-Life Balance", "Mental Health",
            "Resilience", "Goal Setting", "Time Management", "Communication Skills",
            "Leadership", "Teamwork", "Problem Solving", "Critical Thinking",
            "Creativity", "Digital Literacy", "SA Youth Platform", "MYOM",
            "Transitions", "Hope Building", "Action Planning", "Motivation"
        ]

    # Initialize templates
    for content_type, template in default_templates.items():
        template_key = f"template_{content_type}"
        if template_key not in st.session_state:
            st.session_state[template_key] = template

def generate_content_tab():
    """Render the Generate Content tab."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Content type selection
        content_type = st.selectbox(
            "Content Type",
            options=["Lifehack", "Nudge", "Goal-Setting Advice", "Motivation", "Quote"],
            help="Select the type of content you want to generate"
        )
        
        # Theme selection with dropdown and custom input
        theme_option = st.radio("Theme Selection", ["Choose from bank", "Enter custom theme"])
        
        if theme_option == "Choose from bank":
            selected_themes = st.multiselect(
                "Select themes",
                options=sorted(st.session_state.themes_bank),
                default=st.session_state.selected_themes if st.session_state.selected_themes else None
            )
            st.session_state.selected_themes = selected_themes
            
            theme = ", ".join(selected_themes) if selected_themes else ""
        else:
            theme = st.text_input("Enter custom theme(s) separated by commas")
        
        # Tone selection
        tone = st.selectbox(
            "Tone",
            options=[
                "Inspirational", "Friendly", "Professional", "Casual", 
                "Humorous", "Motivational", "Informative", "Supportive",
                "Direct", "Empathetic", "Encouraging", "Personal", "South African"
            ]
        )
        
        # Content length
        length = st.select_slider(
            "Content Length",
            options=["Very Short", "Short", "Medium", "Long", "Very Long"],
            value="Medium"
        )
        
        # South African context and WhatsApp formatting
        sa_context = st.checkbox("Include South African context", value=True)
        whatsapp_format = st.checkbox("Format for WhatsApp", value=True)
    
    with col2:
        # API Configuration
        st.subheader("API Configuration")
        api_key = st.text_input("Google AI API Key", type="password", 
                              value=st.session_state.get('api_key', ''))
        
        if st.button("Set API Key"):
            if not api_key:
                st.error("Please enter an API key")
            else:
                try:
                    # Validate the API key
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # Test with a simple prompt
                    test_response = model.generate_content("Hello, test request.")
                    
                    # If we get here, the API key is valid
                    st.session_state.api_key = api_key
                    st.session_state.api_key_set = True
                    st.success("API key validated successfully!")
                except Exception as e:
                    st.error(f"API key validation failed: {str(e)}")
    
    # Generate content button
    if st.button("Generate Content", type="primary"):
        if not theme:
            st.error("Please enter a theme or select from the theme bank")
        else:
            with st.spinner("Generating content..."):
                # Prepare the prompt
                final_prompt = theme
                if sa_context:
                    final_prompt += " with South African context"
                
                # Generate content
                try:
                    generated_content = generate_content_with_gemini(
                        final_prompt, 
                        content_type, 
                        tone, 
                        length, 
                        st.session_state.get('api_key')
                    )
                    
                    # WhatsApp formatting
                    if whatsapp_format:
                        generated_content = format_for_whatsapp(generated_content)
                    
                    # Store and display generated content
                    st.session_state.generated_content = generated_content
                    
                    # Display generated content
                    st.subheader("Generated Content")
                    label_class = f"label-{content_type.lower().replace(' ', '').replace('-', '')}"
                    st.markdown(f"""
                    <div class="content-display">
                        <span class="{label_class}">{content_type}</span>
                        <p style="white-space: pre-line; margin-top: 10px;">{generated_content}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Save to Content Bank"):
                            save_to_content_bank(
                                generated_content, 
                                content_type,
                                theme,
                                tone
                            )
                            st.success("Content saved to bank!")
                    
                    with col2:
                        st.download_button(
                            label="Download as Text",
                            data=generated_content,
                            file_name=f"{content_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    with col3:
                        if st.button("Regenerate"):
                            st.experimental_rerun()
                
                except Exception as e:
                    st.error(f"Error generating content: {str(e)}")

def generate_content_with_gemini(prompt, content_type, tone, length, api_key):
    """Generate content using Google Generative AI Gemini 1.5 Flash."""
    try:
        # Map length to approximate word count
        length_to_words = {
            "Very Short": 20,
            "Short": 50,
            "Medium": 100,
            "Long": 200,
            "Very Long": 300
        }
        word_count = length_to_words.get(length, 100)
        
        # Get the appropriate template
        template_key = f"template_{content_type}"
        if template_key in st.session_state:
            template = st.session_state[template_key]
        else:
            template = default_templates.get(content_type, default_templates["Nudge"])
        
        # South African context
        sa_context_prompt = "Include South African context, examples, and references where appropriate." if "south african" in prompt.lower() else ""
        
        # Format template
        formatted_prompt = template.format(
            theme=prompt,
            tone=tone,
            length=length,
            word_count=word_count,
            sa_context_prompt=sa_context_prompt
        )
        
        # Check if API key is set
        if not api_key:
            return mock_generate_content(prompt, content_type, tone, length)
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create system instruction for specific content type
        system_instruction = f"You are an expert content creator specializing in {content_type.lower()} content. Your goal is to create engaging, practical, and relevant content that resonates with South African audiences."
        
        # Create the generation config
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "text/plain",
        }
        
        # Create safety settings (moderate)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Set up the model - use the gemini-1.5-flash model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Prepare content with system instruction
        prompt_with_instruction = f"{system_instruction}\n\n{formatted_prompt}"
        
        # Generate content
        response = model.generate_content(prompt_with_instruction)
        
        # Check if we have a response
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            # For older versions of the API that might return a different structure
            return response.candidates[0].content.parts[0].text.strip()
            
    except Exception as e:
        # Log the error details for debugging
        st.error(f"Error with Google Generative AI: {str(e)}")
        
        # Return a user-friendly error message
        return f"Error generating content. Please check your API key and try again. If the problem persists, try using mock generation for demonstrations."

def mock_generate_content(prompt, content_type, tone, length):
    """Mock function for content generation that returns realistic examples."""
    mock_responses = {
        "Lifehack": {
            "Very Short": f"📱 Quick tip for {prompt}: Set aside just 5 minutes each morning to review your goals. This small habit creates massive momentum!",
            "Short": f"⏱️ {tone.upper()} PRODUCTIVITY HACK: Write tomorrow's to-do list before going to bed. When tackling {prompt}, this simple evening routine primes your brain to work on solutions overnight and helps you start the day with clear direction. Try it for one week!",
            "Medium": f"🔥 LEVEL UP YOUR {prompt.upper()} GAME 🔥\n\n1️⃣ Start with just 10 minutes daily\n2️⃣ Use the 'two-minute rule' - if it takes less than 2 mins, do it now\n3️⃣ Track your progress visually\n4️⃣ Celebrate small wins\n\nConsistent small steps lead to massive results over time! Which step will you try first?",
            "Long": f"💪 {tone.upper()} LIFEHACK: THE 30-DAY {prompt.upper()} CHALLENGE 💪\n\nStruggling with {prompt}? Here's a proven system that works:\n\n1. Start ridiculously small (think 1% improvement)\n2. Stack your new habit onto existing routines\n3. Create visual triggers in your environment\n4. Use the 'don't break the chain' method on a calendar\n5. Find an accountability partner\n\nRemember: Motivation follows action, not the other way around! When you take that first tiny step, your brain releases dopamine that makes the next step easier.\n\nWhich of these techniques will you try today? Reply with your commitment! 💯",
            "Very Long": f"🚀 THE ULTIMATE {prompt.upper()} SYSTEM: 5 SCIENCE-BACKED STEPS 🚀\n\nFrustrated with slow progress on {prompt}? You're not alone! After working with thousands of South African youth, we've developed this proven framework:\n\n1️⃣ CLARITY IS POWER\n- Define exactly what success looks like for your {prompt} goals\n- Write it down in present tense as if already achieved\n- Create a vision board with images representing your success\n\n2️⃣ THE 1% RULE\n- Break your goal into ridiculously small daily actions\n- Each step should take less than 5 minutes\n- Focus on consistency, not intensity\n\n3️⃣ ENVIRONMENT DESIGN\n- Remove friction from positive habits\n- Add friction to negative habits\n- Use visual cues in your space (sticky notes, reminders)\n\n4️⃣ ACCOUNTABILITY SYSTEM\n- Find a buddy with similar goals\n- Schedule weekly check-ins\n- Share your progress on social media\n\n5️⃣ CELEBRATION PROTOCOL\n- Celebrate small wins daily\n- Document your progress journey\n- Reflect monthly on how far you've come\n\nTHE BOTTOM LINE: Success with {prompt} isn't about motivation—it's about systems. Which of these steps will you implement today? Let us know! 🔥"
        },
        # Rest of the mock responses from the previous implementation
    }
    
    # Default to medium length if not found
    if length not in mock_responses[content_type]:
        length = "Medium"
    
    return mock_responses[content_type][length]

def format_for_whatsapp(text):
    """Format text for WhatsApp by limiting length and ensuring readability."""
    # Truncate very long texts
    if len(text) > 1000:
        text = text[:997] + "..."
    
    return text

def save_to_content_bank(content, content_type, theme, tone):
    """Save generated content to the content bank."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_id = str(uuid.uuid4())
    
    content_item = {
        "id": unique_id,
        "content": content,
        "type": content_type,
        "theme": theme,
        "tone": tone,
        "timestamp": timestamp
    }
    
    st.session_state.content_bank.append(content_item)

def content_bank_tab():
    """Render the Content Bank tab."""
    st.subheader("Content Bank")
    st.write("View, filter, and export your saved content.")
    
    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        filter_type = st.multiselect(
            "Filter by Type",
            options=["Lifehack", "Nudge", "Goal-Setting Advice", "Motivation", "Quote"],
            default=[]
        )
    
    with filter_col2:
        filter_theme = st.text_input("Filter by Theme (comma-separated)")
    
    with filter_col3:
        filter_tone = st.multiselect(
            "Filter by Tone",
            options=[
                "Inspirational", "Friendly", "Professional", "Casual", 
                "Humorous", "Motivational", "Informative", "Supportive",
                "Direct", "Empathetic", "Encouraging", "Personal", "South African"
            ],
            default=[]
        )
    
    # Apply filters
    filtered_content = st.session_state.content_bank
    
    if filter_type:
        filtered_content = [item for item in filtered_content if item["type"] in filter_type]
    
    if filter_theme:
        themes = [theme.strip().lower() for theme in filter_theme.split(",")]
        filtered_content = [item for item in filtered_content if any(theme in item["theme"].lower() for theme in themes)]
    
    if filter_tone:
        filtered_content = [item for item in filtered_content if item["tone"] in filter_tone]
    
    # Sort by timestamp (newest first)
    filtered_content.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Display content
    if not filtered_content:
        st.info("No content found in the bank. Generate some content to see it here!")
    else:
        # Export options
        export_col1, export_col2 = st.columns([1, 4])
        with export_col1:
            if st.button("Export as CSV"):
                # Convert to DataFrame for easy CSV export
                df = pd.DataFrame(filtered_content)
                csv_data = df.to_csv(index=False)
                
                filename = f"content_bank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
        
        with export_col2:
            st.write(f"Displaying {len(filtered_content)} of {len(st.session_state.content_bank)} items")
        
        # Display each content item
        for item in filtered_content:
            # Determine label class based on content type
            label_class_map = {
                "Lifehack": "label-lifehack",
                "Nudge": "label-nudge",
                "Goal-Setting Advice": "label-goal",
                "Motivation": "label-motivation",
                "Quote": "label-quote"
            }
            label_class = label_class_map.get(item["type"], "label-nudge")
            
            # Display content item
            st.markdown(f"""
            <div class="content-display">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span class="{label_class}">{item["type"]}</span>
                    <small style="color: #6c757d;">{item["timestamp"]}</small>
                </div>
                <p style="white-space: pre-line;">{item["content"]}</p>
                <div style="margin-top: 10px; font-size: 0.9em; color: #6c757d;">
                    <strong>Theme:</strong> {item["theme"]} | <strong>Tone:</strong> {item["tone"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"Copy {item['id'][:8]}", key=f"copy_{item['id']}"):
                    st.toast("Content copied to clipboard!", icon="📋")
                    try:
                        import pyperclip
                        pyperclip.copy(item["content"])
                    except:
                        st.text_area("Copy this text:", value=item["content"], height=100)
            
            with col2:
                st.download_button(
                    label=f"Download {item['id'][:8]}",
                    data=item["content"],
                    file_name=f"{item['type'].lower().replace(' ', '_')}_{item['id'][:8]}.txt",
                    mime="text/plain",
                    key=f"download_{item['id']}"
                )
            
            with col3:
                if st.button(f"Remove {item['id'][:8]}", key=f"remove_{item['id']}"):
                    st.session_state.content_bank = [
                        content for content in st.session_state.content_bank 
                        if content['id'] != item['id']
                    ]
                    st.experimental_rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)

def batch_processing_tab():
    """Render the Batch Processing tab."""
    st.subheader("Batch Content Generation")
    st.write("Generate multiple content pieces based on themes and types.")
    
    # Input method selection
    input_method = st.radio(
        "Select Input Method", 
        ["Manual Entry", "Upload CSV", "Use Theme Bank"]
    )
    
    # Theme input based on method
    if input_method == "Manual Entry":
        themes_input = st.text_area(
            "Enter themes (one per line)", 
            height=150,
            help="Enter one theme per line. You can add emojis too."
        )
        batch_themes = [theme.strip() for theme in themes_input.split("\n") if theme.strip()] if themes_input else []
    
    elif input_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV with themes", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if "theme" in df.columns:
                    batch_themes = df["theme"].dropna().tolist()
                    st.success(f"Found {len(batch_themes)} themes in CSV")
                else:
                    st.error("CSV must contain a 'theme' column")
                    batch_themes = []
            except Exception as e:
                st.error(f"Error processing CSV: {str(e)}")
                batch_themes = []
        else:
            batch_themes = []
    
    else:  # Use Theme Bank
        batch_themes = st.multiselect(
            "Select themes from bank",
            options=sorted(st.session_state.themes_bank)
        )
    
    # Display selected themes
    if batch_themes:
        st.markdown("### Selected Themes")
        themes_display = ", ".join(batch_themes)
        st.info(themes_display)
    
    # Content type selection
    batch_types = st.multiselect(
        "Select content types to generate",
        options=["Lifehack", "Nudge", "Goal-Setting Advice", "Motivation", "Quote"],
        default=["Nudge"]
    )
    
    # Generation settings
    batch_tone = st.selectbox(
        "Tone for all content",
        options=[
            "Inspirational", "Friendly", "Professional", "Casual", 
            "Humorous", "Motivational", "Informative", "Supportive",
            "Direct", "Empathetic", "Encouraging", "Personal", "South African"
        ]
    )
    
    batch_length = st.select_slider(
        "Content Length",
        options=["Very Short", "Short", "Medium", "Long", "Very Long"],
        value="Short"
    )
    
    # Formatting options
    sa_context = st.checkbox("Include South African context for all", value=True)
    whatsapp_format = st.checkbox("Format all for WhatsApp", value=True)
    
    # Generate batch content
    if st.button("Generate Batch Content", type="primary", disabled=not batch_themes or not batch_types):
        # Validate API key
        api_key = st.session_state.get('api_key')
        
        if not api_key and not st.session_state.api_key_set:
            st.warning("Using mock generation. Set an API key for actual content generation.")
        
        # Prepare progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Generate content for each theme and type
        batch_results = []
        total_items = len(batch_themes) * len(batch_types)
        current_item = 0
        
        for theme in batch_themes:
            for content_type in batch_types:
                # Update progress
                current_item += 1
                progress_percentage = current_item / total_items
                progress_bar.progress(progress_percentage)
                
                # Status update
                status_text.info(
                    f"Generating {content_type} for '{theme}'... "
                    f"({current_item}/{total_items})"
                )
                
                # Prepare prompt
                final_prompt = theme
                if sa_context:
                    final_prompt += " with South African context"
                
                # Generate content
                try:
                    generated_content = generate_content_with_gemini(
                        final_prompt, 
                        content_type, 
                        batch_tone, 
                        batch_length, 
                        api_key
                    )
                    
                    # WhatsApp formatting
                    if whatsapp_format:
                        generated_content = format_for_whatsapp(generated_content)
                    
                    # Save to content bank and results
                    save_to_content_bank(
                        generated_content, 
                        content_type, 
                        theme, 
                        batch_tone
                    )
                    
                    batch_results.append({
                        "theme": theme,
                        "content_type": content_type,
                        "content": generated_content,
                        "tone": batch_tone
                    })
                
                except Exception as e:
                    st.error(f"Error generating content for {theme} - {content_type}: {str(e)}")
        
# Completion
        status_text.success(f"Generated {len(batch_results)} content pieces!")
        
        # Convert results to DataFrame for display and export
        if batch_results:
            # Display results DataFrame
            df = pd.DataFrame(batch_results)
            st.dataframe(df[['theme', 'content_type', 'content']])
            
            # Export options
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                # CSV Export
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"batch_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with export_col2:
                # Text Export with all content
                text_content = ""
                for item in batch_results:
                    text_content += f"Theme: {item['theme']}\n"
                    text_content += f"Type: {item['content_type']}\n"
                    text_content += f"Tone: {item['tone']}\n"
                    text_content += f"Content:\n{item['content']}\n"
                    text_content += "-" * 80 + "\n\n"
                
                st.download_button(
                    label="Download as Text",
                    data=text_content,
                    file_name=f"batch_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            # Sample content display
            if batch_results:
                st.subheader("Sample Generated Content")
                sample = batch_results[0]
                
                # Determine label class
                label_class_map = {
                    "Lifehack": "label-lifehack",
                    "Nudge": "label-nudge",
                    "Goal-Setting Advice": "label-goal",
                    "Motivation": "label-motivation",
                    "Quote": "label-quote"
                }
                label_class = label_class_map.get(sample['content_type'], "label-nudge")
                
                # Display sample content
                st.markdown(f"""
                <div class="content-display">
                    <span class="{label_class}">{sample["content_type"]}</span>
                    <p style="white-space: pre-line; margin-top: 10px;">{sample["content"]}</p>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #6c757d;">
                        <strong>Theme:</strong> {sample["theme"]} | <strong>Tone:</strong> {sample["tone"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def settings_tab():
    """Render the Settings tab for theme and template management."""
    st.subheader("Application Settings")
    st.write("Configure themes, prompts, and API settings.")
    
    # Create tabs for different settings
    settings_tab1, settings_tab2, settings_tab3 = st.tabs(
        ["Theme Management", "API Configuration", "Prompt Templates"]
    )
    
    # Theme Management Tab
    with settings_tab1:
        st.subheader("Theme Management")
        
        # Current themes display
        st.markdown("### Current Theme Bank")
        themes_df = pd.DataFrame({"Themes": sorted(st.session_state.themes_bank)})
        st.dataframe(themes_df, use_container_width=True)
        
        # Add new themes
        st.markdown("### Add New Themes")
        new_themes = st.text_area(
            "Enter new themes (one per line)",
            height=100,
            placeholder="e.g.,\nFinancial Wellness\nCareer Transition\nMental Health"
        )
        
        if st.button("Add Themes"):
            if new_themes:
                themes_to_add = [theme.strip() for theme in new_themes.split("\n") if theme.strip()]
                
                # Filter out existing themes
                new_unique_themes = [theme for theme in themes_to_add if theme not in st.session_state.themes_bank]
                
                if new_unique_themes:
                    st.session_state.themes_bank.extend(new_unique_themes)
                    st.success(f"Added {len(new_unique_themes)} new themes!")
                    st.experimental_rerun()
                else:
                    st.warning("No new unique themes to add.")
        
        # Remove themes
        st.markdown("### Remove Themes")
        themes_to_remove = st.multiselect(
            "Select themes to remove",
            options=sorted(st.session_state.themes_bank)
        )
        
        if st.button("Remove Selected Themes"):
            if themes_to_remove:
                for theme in themes_to_remove:
                    if theme in st.session_state.themes_bank:
                        st.session_state.themes_bank.remove(theme)
                
                st.success(f"Removed {len(themes_to_remove)} themes!")
                st.experimental_rerun()
            else:
                st.warning("No themes selected for removal.")
        
        # Export/Import themes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Export Themes")
            themes_json = json.dumps({"themes": sorted(st.session_state.themes_bank)}, indent=2)
            st.download_button(
                label="Export Themes as JSON",
                data=themes_json,
                file_name="theme_bank.json",
                mime="application/json"
            )
        
        with col2:
            st.markdown("### Import Themes")
            uploaded_themes = st.file_uploader("Upload Themes JSON", type=["json"])
            
            if uploaded_themes is not None:
                try:
                    themes_data = json.load(uploaded_themes)
                    if "themes" in themes_data and isinstance(themes_data["themes"], list):
                        # Merge with existing themes
                        st.session_state.themes_bank = list(set(st.session_state.themes_bank + themes_data["themes"]))
                        st.success(f"Imported themes! Bank now has {len(st.session_state.themes_bank)} themes.")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid themes JSON format.")
                except Exception as e:
                    st.error(f"Error importing themes: {str(e)}")
    
    # API Configuration Tab
    with settings_tab2:
        st.subheader("API Configuration")
        
        # API Key Input
        api_key = st.text_input(
            "Google AI API Key", 
            type="password", 
            value=st.session_state.get('api_key', ''),
            help="Enter your Google Generative AI API key"
        )
        
        # Advanced API Settings
        with st.expander("Advanced Settings"):
            temperature = st.slider(
                "Temperature", 
                min_value=0.0, 
                max_value=1.0, 
                value=st.session_state.get('temperature', 0.7),
                step=0.1,
                help="Controls randomness: Lower values are more focused, higher values more creative"
            )
            top_k = st.slider(
                "Top K", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.get('top_k', 40),
                help="Limits token selection to the top k most likely tokens"
            )
            top_p = st.slider(
                "Top P", 
                min_value=0.0, 
                max_value=1.0, 
                value=st.session_state.get('top_p', 0.95),
                step=0.05,
                help="Nucleus sampling: Limits token selection to a cumulative probability"
            )
        
        # Validate and Save API Key
        if st.button("Save API Key"):
            if not api_key:
                st.error("Please enter an API key")
            else:
                try:
                    # Validate the API key
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # Test with a simple prompt
                    test_response = model.generate_content("Hello, test request.")
                    
                    # Save API key and settings
                    st.session_state.api_key = api_key
                    st.session_state.api_key_set = True
                    st.session_state.temperature = temperature
                    st.session_state.top_k = top_k
                    st.session_state.top_p = top_p
                    
                    st.success("API key and settings saved successfully!")
                except Exception as e:
                    st.error(f"API key validation failed: {str(e)}")
        
        # Environment Variable Option
        st.markdown("### Environment Variable")
        st.info(
            "Tip: You can also set the API key using an environment variable "
            "`GOOGLE_API_KEY` in a `.env` file for automatic loading."
        )
    
    # Prompt Templates Tab
    with settings_tab3:
        st.subheader("Prompt Templates")
        
        # Template type selection
        content_type = st.selectbox(
            "Select Content Type", 
            ["Lifehack", "Nudge", "Goal-Setting Advice", "Motivation", "Quote"]
        )
        
        # Get current template
        template_key = f"template_{content_type}"
        current_template = st.session_state.get(template_key, default_templates[content_type])
        
        # Template editing
        edited_template = st.text_area(
            f"Edit {content_type} Template",
            value=current_template,
            height=300,
            help="Use placeholders like {theme}, {tone}, {length}, {word_count}, {sa_context_prompt}"
        )
        
        # Save and Reset buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Template"):
                st.session_state[template_key] = edited_template
                st.success(f"{content_type} template updated!")
        
        with col2:
            if st.button("Reset to Default"):
                st.session_state[template_key] = default_templates[content_type]
                st.success(f"{content_type} template reset to default!")
        
        # Template variables explanation
        st.markdown("### Template Variables")
        st.markdown("""
        | Variable | Description | Example |
        |----------|-------------|---------|
        | {theme} | The content theme | Career Development |
        | {tone} | Desired tone | Motivational |
        | {length} | Content length | Medium |
        | {word_count} | Approximate word count | 100 |
        | {sa_context_prompt} | South African context instruction | Include local references |
        """)

# Footer
st.markdown("""
<div class="footer">
    <p>PromptMe - Content Edition v1.0  | © 2025</p>
</div>
""", unsafe_allow_html=True)

# Main app execution
if __name__ == "__main__":
    main()
