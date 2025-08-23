import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import gc
from src.models.price_forecaster import CardamomPriceForecaster

# Page configuration
st.set_page_config(
    page_title="SpiceHold - AI Cardamom Advisor",
    page_icon="🌶️",
    layout="wide"
)

# Enhanced CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .recommendation-hold {
        background-color: #ffeab9;
        border: 2px solid #ffa726;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        color: #b8860b;
    }
    .recommendation-sell {
        background-color: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        color: #2e7d32;
    }
    .recommendation-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .recommendation-text {
        font-size: 1rem;
        line-height: 1.4;
        margin: 0.4rem 0;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 1rem;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# Cache model loading only
@st.cache_resource
def load_forecasting_model():
    """Load and cache the forecasting model"""
    try:
        forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
        forecaster.load_model('data/models/cardamom_price_model.pkl')
        return forecaster
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def create_dark_forecast_chart(forecast_df, forecast_date):
    """Create dark-themed forecast chart with proper date handling"""
    fig = go.Figure()
    
    # Main prediction line
    fig.add_trace(go.Scatter(
        x=forecast_df['date'],
        y=forecast_df['predicted_price'],
        mode='lines+markers',
        name='Predicted Price',
        line=dict(color='#00AAFF', width=3),
        marker=dict(size=5, color='#00AAFF'),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Price: ₹%{y:,.0f}/kg<extra></extra>'
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=list(forecast_df['date']) + list(forecast_df['date'][::-1]),
        y=list(forecast_df['upper_bound']) + list(forecast_df['lower_bound'][::-1]),
        fill='toself',
        fillcolor='rgba(0, 170, 255, 0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Price Range',
        hoverinfo='skip'
    ))
    
    # Dark theme layout with dynamic title
    fig.update_layout(
        title={
            'text': f'📈 30-Day Cardamom Price Forecast (from {forecast_date.strftime("%b %d, %Y")})',
            'x': 0.5,
            'font': {'size': 16, 'color': 'white'}
        },
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='white', size=12),
        xaxis=dict(
            title='Date',
            gridcolor='#404040',
            tickformat='%b %d',
            showgrid=True,
            color='white'
        ),
        yaxis=dict(
            title='Price (₹/kg)',
            gridcolor='#404040',
            tickformat='₹,.0f',
            showgrid=True,
            color='white'
        ),
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0
        ),
        margin=dict(l=50, r=30, t=60, b=40),
        height=450
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🌶️ SpiceHold</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Cardamom Price Advisor for Kerala Farmers</p>', unsafe_allow_html=True)
    
    # Load model
    forecaster = load_forecasting_model()
    if forecaster is None:
        st.error("Failed to load forecasting model.")
        return
    
    # Initialize session state
    if 'current_forecast_date' not in st.session_state:
        st.session_state.current_forecast_date = None
    
    # Sidebar with form
    with st.sidebar:
        st.markdown("## 📋 Farm Details")
        
        with st.form("farm_details_form"):
            farmer_name = st.text_input("👨‍🌾 Farmer Name", placeholder="Enter your name")
            
            harvest_date = st.date_input(
                "📅 Harvest Date",
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now()
            )
            
            quantity = st.number_input(
                "📦 Quantity (kg)",
                min_value=1,
                max_value=10000,
                value=100,
                step=10
            )
            
            storage_quality = st.selectbox(
                "🏪 Storage Quality",
                ["Excellent (Air-tight, Cool)", "Good (Covered, Dry)", "Average (Basic Storage)"]
            )
            
            location = st.selectbox(
                "📍 Location",
                ["Kumily", "Thekkady", "Vandanmedu", "Kattappana", "Other Kerala"]
            )
            
            forecast_from_date = st.date_input(
                "🔮 Forecast From Date",
                value=datetime.now().date(),
                min_value=datetime.now().date()
            )
            
            # Submit button
            submit_button = st.form_submit_button("🔄 Update Forecast", type="primary")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 🔮 AI Price Forecast")
        
        # Force update when form is submitted OR when date changes OR first load
        should_update = (
            submit_button or 
            st.session_state.current_forecast_date != forecast_from_date or 
            'forecast_data' not in st.session_state
        )
        
        if should_update:
            with st.spinner("Generating forecast..."):
                try:
                    # 🚨 CRITICAL: Force clear ALL related session state
                    for key in ['forecast_data', 'recommendation_data']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Generate NEW forecast with selected date
                    forecast = forecaster.forecast_prices(
                        days_ahead=30,
                        start_date=forecast_from_date
                    )
                    
                    # Get NEW recommendation with SAME date
                    recommendation = forecaster.get_sell_recommendation(
                        days_ahead=30, 
                        start_date=forecast_from_date
                    )
                    
                    # Store FRESH data in session state
                    st.session_state.forecast_data = forecast
                    st.session_state.recommendation_data = recommendation
                    st.session_state.current_forecast_date = forecast_from_date
                    
                    # Success message
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ <strong>Forecast Updated Successfully!</strong> Generated for {forecast_from_date.strftime('%B %d, %Y')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error generating forecast: {e}")
                    return
        
        # Display chart if data exists
        if 'forecast_data' in st.session_state:
            # Create chart with unique key to force refresh
            chart_key = f"forecast_chart_{st.session_state.current_forecast_date}"
            chart = create_dark_forecast_chart(
                st.session_state.forecast_data, 
                st.session_state.current_forecast_date
            )
            st.plotly_chart(chart, use_container_width=True, key=chart_key)
            
            # Show generation info
            st.caption(f"📅 Forecast generated for: **{st.session_state.current_forecast_date.strftime('%B %d, %Y')}**")
        
    with col2:
        st.markdown("## 🎯 AI Recommendation")
        
        if 'recommendation_data' in st.session_state:
            recommendation = st.session_state.recommendation_data
            
            # Display recommendation
            if recommendation['action'] == 'HOLD':
                st.markdown(f'''
                <div class="recommendation-hold">
                    <div class="recommendation-title">🤚 HOLD Your Cardamom</div>
                    <div class="recommendation-text"><strong>Reason:</strong> {recommendation['reason']}</div>
                    <div class="recommendation-text"><strong>Wait:</strong> {recommendation['days_to_wait']} days</div>
                    <div class="recommendation-text"><strong>Optimal Date:</strong> {pd.to_datetime(recommendation['optimal_sell_date']).strftime('%B %d, %Y')}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="recommendation-sell">
                    <div class="recommendation-title">💰 SELL Now!</div>
                    <div class="recommendation-text"><strong>Reason:</strong> {recommendation['reason']}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # Enhanced metrics
            st.markdown("### 📊 Price Metrics")
            
            current_price = recommendation['current_price_estimate']
            optimal_price = recommendation['optimal_price_estimate']
            potential_gain = recommendation['potential_gain_rs_per_kg']
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Current Price", f"₹{current_price:.0f}/kg")
                st.metric("Your Quantity", f"{quantity:,} kg")
            
            with col_b:
                st.metric(
                    "Optimal Price",
                    f"₹{optimal_price:.0f}/kg",
                    f"₹{potential_gain:.0f}/kg" if potential_gain > 0 else None
                )
                st.metric(
                    "Total Potential Gain",
                    f"₹{potential_gain * quantity:,.0f}"
                )
            
            # Risk assessment
            st.markdown("### ⚠️ Risk Assessment")
            
            storage_risks = {
                "Excellent (Air-tight, Cool)": ("Low", "🟢"),
                "Good (Covered, Dry)": ("Medium", "🟡"),
                "Average (Basic Storage)": ("High", "🔴")
            }
            
            risk_level, risk_icon = storage_risks[storage_quality]
            st.write(f"{risk_icon} **Storage Risk:** {risk_level}")
            
            days_since_harvest = (datetime.now().date() - harvest_date).days
            if days_since_harvest < 15:
                st.write("🟢 **Freshness:** Excellent (< 15 days)")
            elif days_since_harvest < 30:
                st.write("🟡 **Freshness:** Good (15-30 days)")
            else:
                st.write("🔴 **Freshness:** Monitor closely (> 30 days)")
        else:
            st.info("👆 Click 'Update Forecast' to generate AI recommendations")
    
    # Debug section (optional - comment out for production)
    if st.sidebar.checkbox("🔍 Show Debug Info"):
        st.markdown("---")
        st.markdown("### Debug Information")
        if 'current_forecast_date' in st.session_state:
            st.write(f"**Current forecast date:** {st.session_state.current_forecast_date}")
        if 'forecast_data' in st.session_state:
            forecast_df = st.session_state.forecast_data
            st.write(f"**Forecast data shape:** {len(forecast_df)} rows")
            st.write(f"**Date range:** {forecast_df['date'].min()} to {forecast_df['date'].max()}")
            st.write(f"**Price range:** ₹{forecast_df['predicted_price'].min():.0f} - ₹{forecast_df['predicted_price'].max():.0f}")

if __name__ == "__main__":
    main()
