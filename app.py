import streamlit as st
import pandas as pd
import json
from datetime import datetime
from src.boq_builder import BOQBuilder
from src.boq_parser import BOQParser
from src.boq_exporter import export_to_excel

st.set_page_config(page_title="BOQ Builder", page_icon="📋", layout="wide")

# Initialize session state
if 'boq_data' not in st.session_state:
    st.session_state.boq_data = None
if 'items' not in st.session_state:
    st.session_state.items = []

st.title("📊 BOQ Builder & Analyzer")
st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🏗️ Build BOQ",
    "📤 Upload & Parse",
    "📊 Analyze",
    "⚙️ Settings"
])

# ============== TAB 1: BUILD BOQ ==============
with tab1:
    st.header("Build New BOQ from Items")
    st.markdown("`Simple: Item + Quantity + Price → Complete BOQ Summary`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Project Information")
        project_name = st.text_input("Project Name:", value="AIMS Square Phase-02")
        project_location = st.text_input("Project Location:", value="Yanbu")
        cq_number = st.text_input("CQ Number:", value="CQ-2025-JED-0088")
        timeframe = st.text_input("Project Timeframe:", value="09 Months")
    
    with col2:
        st.subheader("👤 Salesman Information")
        salesman_first = st.text_input("First Name:", value="Naseeb")
        salesman_last = st.text_input("Last Name:", value="Zada")
        position = st.text_input("Position:", value="Regional Sales Manager")
        branch = st.text_input("Branch:", value="JED")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏢 Customer Information")
        customer_name = st.text_input("Customer Name:", value="Aims")
        owner_name = st.text_input("Owner Name:", value="Holiday Inn Yanbu")
        contact_person = st.text_input("Contact Person:", value="Bilal Nouruldeen Ajaj")
        contact_email = st.text_input("Email:", value="bajaj@aims.com")
    
    with col4:
        st.subheader("💰 Financial Settings")
        margin_percent = st.slider("Profit Margin %:", 0, 100, 28)
        po_value = st.number_input("PO Value (SAR):", value=214192.82)
        scope_of_work = st.text_input("Scope of Work:", value="MA+SVR")
    
    st.markdown("---")
    st.subheader("📦 Add Items")
    
    # Items input section
    col_item, col_qty, col_price, col_supplier = st.columns([2, 1, 1.5, 1.5])
    
    with col_item:
        item_name = st.text_input("Item Description:", key="item_name")
    with col_qty:
        quantity = st.number_input("Quantity:", value=1, min_value=1, key="qty")
    with col_price:
        unit_price = st.number_input("Unit Price (SAR):", value=0.0, key="price")
    with col_supplier:
        supplier = st.selectbox("Supplier:", ["Hikvision", "Ruijie", "Ubiquiti", "Other"], key="supplier")
    
    if st.button("➕ Add Item", key="add_item"):
        if item_name and quantity > 0 and unit_price > 0:
            st.session_state.items.append({
                'description': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'supplier': supplier,
                'total': quantity * unit_price
            })
            st.success(f"✅ Added: {item_name}")
            st.rerun()
        else:
            st.error("❌ Please fill all fields with valid values")
    
    # Display items table
    if st.session_state.items:
        st.subheader("📋 Items List")
        items_df = pd.DataFrame(st.session_state.items)
        items_df['total'] = items_df['quantity'] * items_df['unit_price']
        
        st.dataframe(items_df, use_container_width=True, hide_index=True)
        
        # Delete item option
        col1, col2 = st.columns(2)
        with col1:
            delete_idx = st.selectbox("Delete Item:", range(len(st.session_state.items)), format_func=lambda x: st.session_state.items[x]['description'])
            if st.button("🗑️ Remove Item"):
                st.session_state.items.pop(delete_idx)
                st.rerun()
        
        with col2:
            st.metric("Total Items Cost", f"SAR {items_df['total'].sum():,.2f}")
        
        st.markdown("---")
        
        # Generate BOQ
        if st.button("🚀 Generate Complete BOQ Summary", key="generate_boq"):
            builder = BOQBuilder(
                project_name=project_name,
                project_location=project_location,
                cq_number=cq_number,
                timeframe=timeframe,
                salesman_first=salesman_first,
                salesman_last=salesman_last,
                position=position,
                branch=branch,
                customer_name=customer_name,
                owner_name=owner_name,
                contact_person=contact_person,
                contact_email=contact_email,
                margin_percent=margin_percent,
                po_value=po_value,
                scope_of_work=scope_of_work,
                items=st.session_state.items
            )
            
            st.session_state.boq_data = builder.generate()
            st.success("✅ BOQ Summary Generated!")
            st.rerun()
    
    # Display generated BOQ
    if st.session_state.boq_data:
        st.markdown("---")
        st.subheader("📄 Generated BOQ Summary")
        
        # Show key metrics
        boq = st.session_state.boq_data
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cost", f"SAR {boq['cost_summary']['total_cost']:,.2f}")
        col2.metric("Profit Margin", f"SAR {boq['cost_summary']['profit_margin']:,.2f}")
        col3.metric("Selling Price", f"SAR {boq['cost_summary']['selling_price']:,.2f}")
        col4.metric("Margin %", f"{margin_percent}%")
        
        # Cost breakdown
        with st.expander("💰 Cost Summary", expanded=True):
            cost_df = pd.DataFrame([
                {"Category": "Materials", "Value (SAR)": f"{boq['cost_summary']['materials']:,.2f}"},
                {"Category": "In House", "Value (SAR)": f"{boq['cost_summary']['in_house']:,.2f}"},
                {"Category": "Subcontractor", "Value (SAR)": f"{boq['cost_summary']['subcontractor']:,.2f}"},
                {"Category": "Logistics", "Value (SAR)": f"{boq['cost_summary']['logistics']:,.2f}"},
                {"Category": "Financial Charges", "Value (SAR)": f"{boq['cost_summary']['financial_charges']:,.2f}"},
            ])
            st.dataframe(cost_df, use_container_width=True, hide_index=True)
        
        # Invoicing schedule
        with st.expander("📅 Invoicing Schedule", expanded=True):
            invoicing_df = pd.DataFrame(boq['invoicing'])
            st.dataframe(invoicing_df, use_container_width=True, hide_index=True)
        
        # Supplier breakdown
        with st.expander("🏭 Supplier Quotes", expanded=True):
            supplier_df = pd.DataFrame(boq['suppliers'])
            st.dataframe(supplier_df, use_container_width=True, hide_index=True)
        
        # Export options
        st.markdown("---")
        st.subheader("💾 Export BOQ")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export as JSON
            json_str = json.dumps(boq, indent=2, default=str)
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"BOQ_{cq_number}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        with col2:
            # Export as Excel
            excel_file = export_to_excel(boq, cq_number)
            st.download_button(
                label="📊 Download as Excel",
                data=excel_file,
                file_name=f"BOQ_{cq_number}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            # Export as CSV
            csv_str = pd.DataFrame(st.session_state.items).to_csv(index=False)
            st.download_button(
                label="📋 Download as CSV",
                data=csv_str,
                file_name=f"BOQ_Items_{cq_number}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Clear button
        if st.button("🔄 Start New BOQ"):
            st.session_state.items = []
            st.session_state.boq_data = None
            st.rerun()

# ============== TAB 2: UPLOAD & PARSE ==============
with tab2:
    st.header("Upload & Parse Existing BOQ")
    st.markdown("`Upload Excel/CSV BOQ → Auto-extract & Analyze`")
    
    uploaded_file = st.file_uploader(
        "Choose a BOQ file:",
        type=['xlsx', 'csv', 'xls']
    )
    
    if uploaded_file:
        try:
            parser = BOQParser()
            parsed_data = parser.parse(uploaded_file)
            
            st.success("✅ BOQ Parsed Successfully!")
            
            # Display parsed data
            with st.expander("📋 Project Information"):
                st.json(parsed_data.get('project_info', {}))
            
            with st.expander("👤 Salesman Information"):
                st.json(parsed_data.get('salesman_info', {}))
            
            with st.expander("🏢 Customer Information"):
                st.json(parsed_data.get('customer_info', {}))
            
            with st.expander("💰 Cost Summary"):
                cost_df = pd.DataFrame([parsed_data.get('cost_summary', {})])
                st.dataframe(cost_df, use_container_width=True)
            
            with st.expander("📦 Items"):
                items_df = pd.DataFrame(parsed_data.get('items', []))
                st.dataframe(items_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error parsing file: {str(e)}")

# ============== TAB 3: ANALYZE ==============
with tab3:
    st.header("📊 BOQ Analysis")
    
    if st.session_state.boq_data:
        boq = st.session_state.boq_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Items", len(st.session_state.items))
        with col2:
            st.metric("Total Cost", f"SAR {boq['cost_summary']['total_cost']:,.0f}")
        with col3:
            st.metric("Profit", f"SAR {boq['cost_summary']['profit_margin']:,.0f}")
        
        # Cost breakdown chart
        st.subheader("Cost Breakdown")
        cost_data = {
            'Materials': boq['cost_summary']['materials'],
            'In House': boq['cost_summary']['in_house'],
            'Subcontractor': boq['cost_summary']['subcontractor'],
            'Logistics': boq['cost_summary']['logistics'],
            'Financial': boq['cost_summary']['financial_charges']
        }
        st.bar_chart(cost_data)
        
        # Invoicing timeline
        st.subheader("Invoicing Payment Schedule")
        invoicing_df = pd.DataFrame(boq['invoicing'])
        st.line_chart(invoicing_df.set_index('Description')['Amount (SAR)'])
    else:
        st.info("📋 Build a BOQ first to see analysis")

# ============== TAB 4: SETTINGS ==============
with tab4:
    st.header("⚙️ Settings & Guide")
    
    st.subheader("📖 BOQ Structure Guide")
    st.markdown("""
    ### Order Information
    - CQ Number
    - Validity period
    - Scope of Work
    
    ### Salesman Information
    - Name, Position, Branch
    - Contact details
    
    ### Project Information
    - Project name and location
    - Timeline
    - Customer details
    
    ### Cost Summary
    - Materials, Labor, Subcontractor, Logistics
    - Financial charges
    - Margin calculation
    
    ### Invoicing Schedule
    - Payment milestones (50%, 40%, 5%, 5%)
    - Due dates
    
    ### Supplier Quotes
    - Vendor information
    - Quote references
    - Cost breakdown
    
    ### Approvals
    - Design & Estimation Manager
    - Project Manager
    - Sales Manager
    - PMO, Logistics, CFO, COO, CEO
    """)
    
    st.subheader("📋 BOQ Builder Features")
    st.markdown("""
    ✅ **Automatic Calculations**
    - Total costs with margins
    - Profit calculations
    - Invoice amounts
    
    ✅ **Multiple Export Formats**
    - Excel (with formatting)
    - JSON (for APIs)
    - CSV (for data analysis)
    
    ✅ **Smart Parsing**
    - Upload existing BOQs
    - Auto-detect structure
    - Extract data accurately
    """)
