import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, List, Optional

# Configuration
# Auto-detect API URL based on environment
import os
if os.getenv("SPACE_ID"):  # Hugging Face Spaces
    FASTAPI_URL = "http://localhost:8000"
elif os.getenv("RENDER"):  # Render.com
    FASTAPI_URL = "http://localhost:8000"
else:  # Local development
    FASTAPI_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="FOMC Statement Classifier",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .classification-result {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .historical-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
    """Make API request to FastAPI backend"""
    try:
        url = f"{FASTAPI_URL}{endpoint}"
        
        if method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, data=json.dumps(data))
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to the backend API at {FASTAPI_URL}. Please ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def format_confidence(confidence: float) -> str:
    """Format confidence score with color coding"""
    percentage = confidence * 100
    if percentage >= 80:
        return f'<span class="confidence-high">{percentage:.1f}%</span>'
    elif percentage >= 60:
        return f'<span class="confidence-medium">{percentage:.1f}%</span>'
    else:
        return f'<span class="confidence-low">{percentage:.1f}%</span>'

def display_classification_results(results: Dict):
    """Display classification results in a formatted way"""
    if not results:
        st.warning("No classification results available.")
        return
    
    # Map API response keys to display names
    display_mapping = {
        "sentiment": "Sentiment",
        "economic_growth": "Economic Growth", 
        "employment_growth": "Employment Growth",
        "inflation": "Inflation",
        "medium_term_rate": "Medium Term Rate",
        "policy_rate": "Policy Rate"
    }
    
    st.subheader("🎯 Classification Results")
    
    for key, display_name in display_mapping.items():
        if key in results:
            result = results[key]
            prediction = result.get("prediction", "N/A")
            confidence = result.get("confidence", 0.0)
            
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{display_name}:** {prediction}")
                with col2:
                    st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)

def home_page():
    """Display the home page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    # Header image placeholder (you can add an actual image here)
    st.markdown("# 🏛️ FOMC Statement Classifier")
    st.markdown("### A financial-domain BERT model for Federal Reserve (FOMC) document analysis.")
    
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h3>
            This project fine-tuned ProsusAI/finBERT using FOMC statements to improve financial NLP tasks.
        </h3>
        <h4>
            ProsusAI → (MLM FineTuning) → fomc_mlm_minutes → (MLM FineTuning) → fomc_mlm_statements → (Classification FineTuning) → FOMC_LLM_VK
        </h4>
        <p style='font-size: 1.1em; margin: 2rem 0;'>
            FOMC Minutes are the detailed records of the Federal Reserve's meetings released late.<br>
            FOMC Statements are concise summaries released immediately after the meeting.<br><br>
            These FOMC data is helpful to guide market expectations and signal the Fed's outlook on Inflation, Economic Growth, and more.<br>
            This model is helpful for classifying these FOMC statements according to 6 attributes:<br>
            <strong>Sentiment, Economic Growth, Employment Growth, Inflation, Medium Term Rate, Policy Rate</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Enter Classification Tool", type="primary", use_container_width=True):
            st.session_state.page = "classification"
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    **Project by:** Vivek Maddula  
    **Research Guide:** Dr. Brindha
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def classification_page():
    """Display the classification page"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Home"):
            st.session_state.page = "home"
            st.rerun()
    
    st.title("🎯 FOMC Statement Classification")
    
    # Create two main columns
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.subheader("📝 Input")
        
        # Historical data section
        with st.expander("📊 Select from Historical Data", expanded=False):
            st.markdown('<div class="historical-section">', unsafe_allow_html=True)
            
            # Get available years
            years_data = make_api_request("/historical/years")
            if years_data and "years" in years_data:
                years = years_data["years"]
                
                selected_year = st.selectbox("Select Year", years, key="year_select")
                
                if selected_year:
                    # Get months for selected year
                    months_data = make_api_request(f"/historical/months/{selected_year}")
                    if months_data and "months" in months_data:
                        months = months_data["months"]
                        month_options = [(m["name"], m["number"]) for m in months]
                        
                        selected_month_name = st.selectbox(
                            "Select Month", 
                            [name for name, _ in month_options],
                            key="month_select"
                        )
                        
                        if selected_month_name:
                            # Get month number
                            selected_month_num = next(num for name, num in month_options if name == selected_month_name)
                            
                            # Get statements for selected year/month
                            statements_data = make_api_request(f"/historical/statements/{selected_year}/{selected_month_num}")
                            if statements_data and "statements" in statements_data:
                                statements = statements_data["statements"]
                                
                                if statements:
                                    statement_options = [
                                        f"{stmt['month_year']} - {stmt['statement_content'][:50]}..."
                                        for stmt in statements
                                    ]
                                    
                                    selected_statement_idx = st.selectbox(
                                        "Select Statement",
                                        range(len(statement_options)),
                                        format_func=lambda x: statement_options[x],
                                        key="statement_select"
                                    )
                                    
                                    if st.button("📥 Load Selected Statement"):
                                        selected_statement = statements[selected_statement_idx]
                                        st.session_state.loaded_text = selected_statement["statement_content"]
                                        st.session_state.actual_values = selected_statement.get("actual_values")
                                        st.success("Statement loaded!")
                                        st.rerun()
                                else:
                                    st.info("No statements available for this period.")
            else:
                st.warning("Historical data not available.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Text input
        default_text = st.session_state.get("loaded_text", "")
        text_input = st.text_area(
            "Enter FOMC Statement Text",
            value=default_text,
            height=200,
            placeholder="Paste FOMC statement text here or select from historical data above...",
            key="text_input"
        )
        
        # Classification button
        if st.button("🎯 Classify Statement", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("Classifying statement..."):
                    results = make_api_request("/classify", "POST", {"text": text_input})
                    if results:
                        st.session_state.classification_results = results
                        st.success("Classification completed!")
                        st.rerun()
            else:
                st.warning("Please enter some text to classify.")
    
    with right_col:
        st.subheader("📊 Results")
        
        # Display classification results
        if "classification_results" in st.session_state:
            display_classification_results(st.session_state.classification_results)
            
            # Show actual values if available
            if "actual_values" in st.session_state and st.session_state.actual_values:
                st.subheader("📋 Actual Values (from Historical Data)")
                actual_values = st.session_state.actual_values
                
                for category, actual_value in actual_values.items():
                    st.markdown(f"**{category}:** {actual_value}")
        else:
            st.info("Results will appear here after classification...")
        
        # Label mappings reference
        st.subheader("📚 Label Mappings Reference")
        
        # Get label mappings from API
        mappings_data = make_api_request("/label-mappings")
        if mappings_data and "label_maps" in mappings_data:
            label_maps = mappings_data["label_maps"]
            
            # Create a nice table
            mapping_data = []
            for category, labels in label_maps.items():
                labels_str = ", ".join(labels.keys())
                mapping_data.append({"Category": category, "Labels": labels_str})
            
            df_mappings = pd.DataFrame(mapping_data)
            st.dataframe(df_mappings, use_container_width=True, hide_index=True)
        else:
            # Fallback static mappings
            st.markdown("""
            | Category | Labels |
            |----------|--------|
            | **Sentiment** | Positive, Neutral, Negative |
            | **Economic Growth** | UP, Down, Flat |
            | **Employment Growth** | UP, Down, Flat |
            | **Inflation** | UP, Down, Flat |
            | **Medium Term Rate** | Hawk, Dove |
            | **Policy Rate** | Raise, Flat, Lower |
            """)

def main():
    """Main application logic"""
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Check API health
    health_data = make_api_request("/health")
    if health_data:
        if health_data.get("status") != "healthy":
            st.warning("⚠️ Backend API is not fully healthy. Some features may not work properly.")
    
    # Route to appropriate page
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "classification":
        classification_page()

if __name__ == "__main__":
    main()

