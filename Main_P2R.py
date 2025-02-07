import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st
import json

# Load your logo image
logo_url = "Images/LCY3 Logo.png"
# Streamlit UI Setup
st.set_page_config(page_title="LCY3 P2R Coveyor Capacity", layout="wide")
# Create layout with three columns
col1, col2, col3 = st.columns([1, 5, 2])  # Adjust column widths as needed

# Display the logo
with col1:
    st.image(logo_url, width=150)  # Adjust width for a bigger logo

# Display the title
with col2:
    st.title("LCY3 P2R Conveyor Capacity")

# Placeholder for the date and time (updates dynamically)
with col3:
    st.subheader('Last successful sync')
    time_hold = st.empty()  # Reserve space for the time display
st.write('Developed by @aakalkri for LCY3 under supervision of @didymiod. Chime during office hours for more feedbacks and suggestions.')
with st.expander('Chart Info'):
    st.write(f"✅ Green indicates safe levels. 🟡 Orange signals a warning threshold. 🔴 Red represents critical capacity.")
    st.write(f"Charts update every minute.")
    
# Display the logo in the sidebar
st.sidebar.image(logo_url, width=300)

# Sidebar for User-Defined Thresholds
threshold_1 = st.sidebar.number_input(
    "Set Threshold 1 (Lower Limit)", 
    min_value=1, 
    max_value=10000, 
    value=1500, 
    step=100
)

# Ensuring Threshold 2 is Valid
if "threshold_2" not in st.session_state or threshold_1 >= st.session_state["threshold_2"]:
    st.session_state["threshold_2"] = max(threshold_1 * 1.2, threshold_1 + 10)

threshold_2 = st.sidebar.number_input(
    "Set Threshold 2 (Upper Limit)", 
    min_value=threshold_1 + 1,
    max_value=10000, 
    value=int(st.session_state["threshold_2"]),
    step=100
)

# Update session state to persist the value
st.session_state["threshold_2"] = threshold_2

st.sidebar.markdown(f"✅ **Green Zone:** 0 to {threshold_1}")
st.sidebar.markdown(f"🟡 **Yellow Zone:** {threshold_1} to {threshold_2}")
st.sidebar.markdown(f"🔴 **Red Zone:** Above {threshold_2}")


selected_legends = st.sidebar.multiselect(
    "Select Legends to Display", 
    options=["Sorted_P4", "Sorted_P3", "Sorted_P2"],
    default=["Sorted_P4", "Sorted_P3", "Sorted_P2"]
)


def get_contingency_message(value):
    if value < threshold_1:
        return "Okay"
    elif threshold_1 <= value <= threshold_2:
        return "Run Contingency 1"
    else:
        return "Run Contingency 2"


# Define a function to apply the color styling
def colored_card(title, value, message, color):
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:10px; border-radius:10px; text-align:center; color:white; font-size:18px;">
            <strong>{title}</strong><br>
            <span style="font-size:24px;">{value:,.0f}</span><br>
            <strong>{message}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
# Authentication for Google Sheets using Streamlit Secrets
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Directly access Streamlit secrets and parse them as JSON
    credentials_dict = st.secrets["gcp"] 
    
    # Authenticate using the credentials
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    
    return client

def update_time():
    """Updates the time in the placeholder."""
    current_time = datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    time_hold.markdown(f"<h3 style='text-align: right;'>{current_time}</h3>", unsafe_allow_html=True)

 # Define card colors based on thresholds
def get_card_color(value):
    if value < threshold_1:
        return "green"  # Safe
    elif threshold_1 <= value <= threshold_2:
        return "orange"  # Warning
    else:
        return "red"  # Critical
# Pull data from Google Sheets and convert it to a DataFrame
@st.cache_data(ttl=60)
def pull_data_from_google_sheets(sheet_name):
    client = authenticate_google_sheets()
    sheet = client.open("Data_Pull_Minute").worksheet(sheet_name)
    
    # Get all data from the sheet
    data = sheet.get_all_records()  # This returns a list of dictionaries
    
    # Convert the data into a Pandas DataFrame
    df = pd.DataFrame(data)
    return df

# Importing st_autorefresh
from streamlit_autorefresh import st_autorefresh

def main():
    # Placeholder for the Card
    card_container = st.empty()

    # Live Graph Streaming
    graph_container = st.empty()

    # Auto-refresh every 60 seconds
    st_autorefresh(interval=60 * 1000, key="data_refresh")

    while True:
        df_pivoted = pull_data_from_google_sheets('Sheet1')
        data = pull_data_from_google_sheets('Sheet2')
        # Call update_time() inside main or any loop to refresh time
        update_time()
        # Convert the 'Time' column to datetime format (if needed)
        df_pivoted['Time'] = pd.to_datetime(df_pivoted['Time'], errors='coerce')
        data['Time'] = pd.to_datetime(data['Time'], errors='coerce')
        
        df_pivoted.set_index('Time', inplace=True)
        
        # Ensure df_pivoted exists and is not empty
        if not df_pivoted.empty:
            latest_rows = data.groupby("Label").last()

            latest_p4 = latest_rows.loc["Sorted_P4", "Value"] if "Sorted_P4" in latest_rows.index else 0
            latest_p3 = latest_rows.loc["Sorted_P3", "Value"] if "Sorted_P3" in latest_rows.index else 0
            latest_p2 = latest_rows.loc["Sorted_P2", "Value"] if "Sorted_P2" in latest_rows.index else 0

            contingency_p4 = get_contingency_message(latest_p4)
            contingency_p3 = get_contingency_message(latest_p3)
            contingency_p2 = get_contingency_message(latest_p2)

            card_color_p4 = get_card_color(latest_p4)
            card_color_p3 = get_card_color(latest_p3)
            card_color_p2 = get_card_color(latest_p2)

            with card_container:
                col1, col3, col5 = st.columns(3)
                
                with col1:
                    colored_card("P2R P4", latest_p4, contingency_p4, get_card_color(latest_p4))
                    
                with col3:
                    colored_card("P2R P3", latest_p3, contingency_p3, get_card_color(latest_p3))
                
                with col5:
                    colored_card("P2R P2", latest_p2, contingency_p2, get_card_color(latest_p2))

            # Create Interactive Plotly Graph
            fig = go.Figure()

            # Background Color Zones
            fig.add_shape(type="rect", x0=data["Time"].min(), x1=data["Time"].max(),
                        y0=0, y1=threshold_1, fillcolor="green", opacity=0.3, layer="below", line_width=0)
            fig.add_shape(type="rect", x0=data["Time"].min(), x1=data["Time"].max(),
                        y0=threshold_1, y1=threshold_2, fillcolor="yellow", opacity=0.3, layer="below", line_width=0)
            fig.add_shape(type="rect", x0=data["Time"].min(), x1=data["Time"].max(),
                        y0=threshold_2, y1=max(data["Value"].max(), threshold_2 * 1.2),
                        fillcolor="red", opacity=0.3, layer="below", line_width=0)

            for column in selected_legends:
                if column in df_pivoted.columns:
                    fig.add_trace(go.Scatter(x=df_pivoted.index, y=df_pivoted[column], 
                                        mode="lines+markers", name=column,
                                        line=dict(width=2)))

            fig.update_layout(
                title="Live Data with Threshold Zones",
                xaxis_title="Time",
                yaxis_title="Value",
                template="plotly_white",
                hovermode="x unified",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ),
                xaxis=dict(
                    range=[data["Time"].min(), data["Time"].max()]
                ),
                autosize=True,
                margin=dict(l=40, r=40, t=40, b=40),
            )

            with graph_container:
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")

        
if __name__ == "__main__":
    main()
