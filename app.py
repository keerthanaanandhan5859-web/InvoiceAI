import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai_extractor import extract_requirements
from pricing import load_pricing, lookup_services
from invoice import calculate_invoice, generate_invoice_number, generate_pdf

load_dotenv()

st.set_page_config(
    page_title="InvoicePilot AI",
    page_icon="🧾",
    layout="wide",
)

defaults = {
    "extracted": None,
    "priced_items": None,
    "invoice_data": None,
    "invoice_number": None,
    "approved": False,
    "history": [],
    "demo_text": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

try:
    pricing_df = load_pricing()
except Exception as exc:
    st.error(f"Pricing database error: {exc}")
    st.stop()

st.markdown("""
<style>
.title {font-size:42px;font-weight:800;margin-bottom:0;}
.subtitle {color:#6B7280;font-size:18px;margin-bottom:30px;}
.step {font-size:24px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🧾 InvoicePilot AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Convert natural-language customer requirements '
    'into verified, review-ready invoices.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Settings")
    tax_rate = st.selectbox("GST / Tax Rate", [0, 5, 12, 18], index=3)
    st.divider()
    st.subheader("🤖 AI")
    if os.getenv("GROQ_API_KEY"):
        st.success("Groq API connected")
    else:
        st.error("Groq API key missing")
    st.divider()
    st.subheader("💰 Pricing Source")
    st.info(f"{len(pricing_df)} approved services")

create_tab, history_tab, pricing_tab = st.tabs(
    ["📝 Create Invoice", "📊 Invoice History", "💰 Pricing Database"]
)

with create_tab:
    st.markdown('<div class="step">1️⃣ Customer Requirement</div>', unsafe_allow_html=True)
    st.write("Enter the customer's requirement in natural language.")

    demo_request = """
Hi, I'm Rahul Kumar from ABC Technologies.

Please arrange 3 website maintenance packages and 2 SEO audits.

My email is rahul@abc.com.

We need them completed this month.
"""

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Load Demo Request", use_container_width=True):
            st.session_state.demo_text = demo_request
            st.rerun()

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            for key in ["demo_text", "extracted", "priced_items", "invoice_data", "invoice_number"]:
                st.session_state[key] = "" if key == "demo_text" else None
            st.session_state.approved = False
            st.rerun()

    customer_text = st.text_area(
        "Customer message",
        value=st.session_state.demo_text,
        height=180,
        placeholder="Example: I am Rahul from ABC Technologies. I need 2 SEO audits...",
    )

    if st.button("🤖 Extract Requirements", type="primary", use_container_width=True):
        if not customer_text.strip():
            st.warning("Please enter a customer requirement.")
        elif not os.getenv("GROQ_API_KEY"):
            st.error("GROQ_API_KEY is not configured.")
        else:
            with st.spinner("Groq AI is extracting requirements..."):
                try:
                    st.session_state.extracted = extract_requirements(customer_text)
                    st.session_state.priced_items = None
                    st.session_state.invoice_data = None
                    st.session_state.approved = False
                    st.session_state.invoice_number = None
                    st.success("AI extraction completed.")
                except Exception as exc:
                    st.error(f"Extraction failed: {exc}")

    if st.session_state.extracted:
        extracted = st.session_state.extracted

        st.divider()
        st.markdown('<div class="step">2️⃣ AI-Extracted Requirements</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 👤 Customer")
            st.write(f"**Name:** {extracted.get('customer_name') or 'Not provided'}")
            st.write(f"**Email:** {extracted.get('email') or 'Not provided'}")
        with c2:
            st.markdown("### 📝 Notes")
            st.write(extracted.get("notes") or "No notes")

        services = extracted.get("services", [])
        st.markdown("### 🛒 Requested Services")
        if services:
            st.dataframe(pd.DataFrame(services), use_container_width=True, hide_index=True)
        else:
            st.warning("No services detected.")

        st.divider()
        st.markdown('<div class="step">3️⃣ Verified Price Lookup</div>', unsafe_allow_html=True)
        st.caption("Prices come from the approved pricing database. Groq does not generate prices.")

        if st.button("🔎 Verify Prices", type="primary", use_container_width=True):
            with st.spinner("Checking pricing database..."):
                st.session_state.priced_items = lookup_services(extracted, pricing_df)
                st.session_state.invoice_data = None
                st.session_state.approved = False

        if st.session_state.priced_items:
            priced_items = st.session_state.priced_items
            rows, missing = [], []

            for item in priced_items:
                if item["found"]:
                    rows.append({
                        "Service": item["matched_name"],
                        "Quantity": item["quantity"],
                        "Unit Price": f"₹{item['unit_price']:,.2f}",
                        "Amount": f"₹{item['unit_price'] * item['quantity']:,.2f}",
                        "Status": "✅ Verified",
                    })
                else:
                    missing.append(item["requested_name"])
                    rows.append({
                        "Service": item["requested_name"],
                        "Quantity": item["quantity"],
                        "Unit Price": "—",
                        "Amount": "—",
                        "Status": "⚠️ Review Required",
                    })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if missing:
                st.error("Missing approved prices: " + ", ".join(missing))
                st.warning("Invoice generation is blocked until missing prices are reviewed.")
            else:
                st.success("All service prices verified.")

                invoice_data = calculate_invoice(priced_items, tax_rate)
                st.session_state.invoice_data = invoice_data

                st.divider()
                st.markdown('<div class="step">4️⃣ Invoice Calculation</div>', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Subtotal", f"₹{invoice_data['subtotal']:,.2f}")
                c2.metric(f"GST ({tax_rate}%)", f"₹{invoice_data['tax_amount']:,.2f}")
                c3.metric("Total", f"₹{invoice_data['total']:,.2f}")

                st.divider()
                st.markdown('<div class="step">5️⃣ Review & Approval</div>', unsafe_allow_html=True)

                if not st.session_state.invoice_number:
                    st.session_state.invoice_number = generate_invoice_number()

                invoice_number = st.session_state.invoice_number
                st.info(f"Invoice Number: **{invoice_number}**")
                st.write(f"**Customer:** {extracted.get('customer_name') or 'N/A'}")
                st.write(f"**Email:** {extracted.get('email') or 'N/A'}")

                review_rows = [
                    {
                        "Service": item["matched_name"],
                        "Qty": item["quantity"],
                        "Unit Price": f"₹{item['unit_price']:,.2f}",
                        "Amount": f"₹{item['amount']:,.2f}",
                    }
                    for item in invoice_data["items"]
                ]
                st.dataframe(pd.DataFrame(review_rows), use_container_width=True, hide_index=True)
                st.markdown(f"## Total: ₹{invoice_data['total']:,.2f}")

                approval = st.checkbox("I have reviewed the invoice and approve it for export.")
                if approval:
                    st.session_state.approved = True

                if st.session_state.approved:
                    st.success("✅ Invoice approved successfully.")

                    pdf_file = generate_pdf(
                        invoice_number,
                        extracted.get("customer_name"),
                        extracted.get("email"),
                        invoice_data["items"],
                        invoice_data["subtotal"],
                        invoice_data["tax_rate"],
                        invoice_data["tax_amount"],
                        invoice_data["total"],
                        extracted.get("notes", ""),
                    )

                    st.download_button(
                        "📄 Download Invoice PDF",
                        data=pdf_file,
                        file_name=f"{invoice_number}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True,
                    )

                    if st.button("💾 Save to Invoice History", use_container_width=True):
                        st.session_state.history.append({
                            "Invoice": invoice_number,
                            "Customer": extracted.get("customer_name") or "Unknown",
                            "Email": extracted.get("email") or "",
                            "Subtotal": invoice_data["subtotal"],
                            "Tax": invoice_data["tax_amount"],
                            "Total": invoice_data["total"],
                            "Status": "Approved",
                        })
                        st.success("Invoice saved to history.")

with history_tab:
    st.subheader("📊 Invoice History")
    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        st.metric("Total Invoiced", f"₹{history_df['Total'].sum():,.2f}")
    else:
        st.info("No invoices created yet.")

with pricing_tab:
    st.subheader("💰 Approved Pricing Database")
    st.caption("This database is the source of truth for service prices.")
    st.dataframe(pricing_df, use_container_width=True, hide_index=True)
