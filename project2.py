import streamlit as st
import pandas as pd

# --- Session State Setup ---
if "members" not in st.session_state:
    st.session_state.members = []
if "bill" not in st.session_state:
    st.session_state.bill = []
if "tax" not in st.session_state:
    st.session_state.tax = 0.0
if "tip" not in st.session_state:
    st.session_state.tip = 0.0

# --- Members Section ---
st.subheader("Add People")

col1, col2 = st.columns([4, 1])
with col1:
    new_member = st.text_input("", placeholder="Add member name (max 30 characters)", max_chars=30)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    add_member = st.button("Add")

if add_member and new_member.strip():
    name = new_member.strip()
    if len(st.session_state.members) >= 12:
        st.error("You can only add up to 12 members.")
    elif name.lower() in [m.lower() for m in st.session_state.members]:
        st.error(f"Member '{name}' already exists. Please enter a unique name.")
    else:
        st.session_state.members.append(name)
        st.rerun()

if st.session_state.members:
    st.markdown("**Current Members:**")
    num_cols = 3
    rows = (len(st.session_state.members) + 2) // 3

    for row in range(rows):
        cols = st.columns(3)
        for i in range(3):
            idx = row * 3 + i
            if idx < len(st.session_state.members):
                with cols[i]:
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(
                                f"<div style='margin: 0 8px 0 8px; padding: 6px; border: 1px solid #ccc; border-radius: 6px; text-align: center; white-space: normal; word-wrap: break-word;'>{st.session_state.members[idx]}</div>",
                                unsafe_allow_html=True
                            )
                        with col2:
                            if st.button("X", key=f"remove_member_{idx}"):
                                del st.session_state.members[idx]
                                # Clean up removed member from assigned bill items
                                for item in st.session_state.bill:
                                    if "Assigned" in item and isinstance(item["Assigned"], list):
                                        item["Assigned"] = [m for m in item["Assigned"] if m in st.session_state.members]
                                st.rerun()

# --- Tax Section ---
st.subheader("Add or Input Bill")
st.markdown("**Please add Tax and Total Amount for Later**")
st.session_state.tax = st.number_input("Tax", min_value=0.0, step=0.01, value=st.session_state.tax)

receipt_subtotal = st.number_input("Receipt Total (pre-tip, optional)", min_value=0.0, step=0.01)
    # Tip input
st.session_state.tip = st.number_input("Tip", min_value=0.0, step=0.01, value=st.session_state.tip)
calculated_subtotal = sum(item["Cost"] for item in st.session_state.bill)
total_with_tax = calculated_subtotal + st.session_state.tax

if receipt_subtotal > 0:
    diff = total_with_tax - receipt_subtotal
    if abs(diff) < 0.01:
        st.success("Taxed subtotal matches receipt.")
    else:
        st.warning(f"Difference from receipt total (pre-tip): ${diff:.2f}")

# --- Bill Entry ---
input_method = st.radio("Choose how to enter the bill (CSV Upload would be a receipt scan)", ["Manual Entry", "Upload CSV"])

if input_method == "Manual Entry":
    with st.form("manual_entry_form"):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            item_name = st.text_input("Item Name", key="item_name")
        with col2:
            item_cost = st.number_input("Cost", min_value=0.0, step=0.01, key="item_cost")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            add_item = st.form_submit_button("Add to Bill")
        if add_item and item_name and item_cost:
            st.session_state.bill.append({
                "Name": item_name,
                "Cost": item_cost,
                "Assigned": []
            })
            st.success(f"Added item '{item_name}' with cost ${item_cost:.2f} to the bill.")
        elif add_item:
            st.error("Both name and cost are required.")

elif input_method == "Upload CSV":
    st.write("CSV must include columns: `Name, Cost`")
    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    if csv_file:
        try:
            df = pd.read_csv(csv_file)
            required_columns = {"Name", "Cost"}
            if required_columns.issubset(df.columns):
                for _, row in df.iterrows():
                    st.session_state.bill.append({
                        "Name": row["Name"],
                        "Cost": row["Cost"],
                        "Assigned": []
                    })
                st.success("CSV uploaded and bill items added.")
            else:
                st.error("CSV must have 'Name' and 'Cost' columns.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

# Show current bill with edit/remove options
if st.session_state.bill:
    st.subheader("Current Bill")
    bill_df = pd.DataFrame(st.session_state.bill)

    item_to_delete = None

    for index, row in bill_df.iterrows():
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            item_name = st.text_input("Item Name", value=row["Name"], key=f"name_{index}")
        with col2:
            item_cost = st.number_input("Cost", value=row["Cost"], min_value=0.0, step=0.01, key=f"cost_{index}")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key=f"remove_item_{index}"):
                item_to_delete = index

        st.session_state.bill[index]["Name"] = item_name
        st.session_state.bill[index]["Cost"] = item_cost

        # Member assignment
        assigned = row.get("Assigned", [])
        st.session_state.bill[index]["Assigned"] = st.multiselect(
            f"Assign to:", options=st.session_state.members,
            default=assigned, key=f"assign_{index}"
        )

    if item_to_delete is not None:
        del st.session_state.bill[item_to_delete]
        st.rerun()

    # Warnings
    assigned_people = set()
    for item in st.session_state.bill:
        assigned_people.update(item.get("Assigned", []))

    unassigned_people = [m for m in st.session_state.members if m not in assigned_people]
    if unassigned_people:
        st.warning(f"These people are not assigned to any items: {', '.join(unassigned_people)}")

    unassigned_items = [item["Name"] for item in st.session_state.bill if not item.get("Assigned")]
    if unassigned_items:
        st.warning(f"These items have no one assigned: {', '.join(unassigned_items)}")



# Totals
subtotal = sum(item["Cost"] for item in st.session_state.bill)
tax = st.session_state.tax
tip = st.session_state.tip
grand_total = subtotal + tax + tip

# Member totals
member_totals = {m: 0.0 for m in st.session_state.members}
for item in st.session_state.bill:
    assigned = item.get("Assigned", [])
    if assigned:
        split_cost = item["Cost"] / len(assigned)
        for m in assigned:
            member_totals[m] += split_cost

# Tax/tip allocation
total_pre_split = sum(member_totals.values())
for m in member_totals:
    share = member_totals[m] / total_pre_split if total_pre_split else 0
    member_totals[m] += tax * share
    member_totals[m] += tip * share

# Display receipt totals
st.markdown("---")
st.markdown(f"**Calculated Subtotal:** ${subtotal:,.2f}")
st.markdown(f"**Tax:** ${tax:,.2f}")
st.markdown(f"**Tip:** ${tip:,.2f}")
st.markdown(f"### Grand Total: **${grand_total:,.2f}**")

# Member Subtotals (pre-tax/tip)
st.markdown("### Totals by Expense")
member_subtotals_df = pd.DataFrame([
    {"Member": m, "Subtotal": f"${member_totals[m]:,.2f}"}
    for m in st.session_state.members
])
st.dataframe(member_subtotals_df, hide_index=True, use_container_width=True)

# Final Amounts
member_final_totals = {}
for m in st.session_state.members:
    share = member_totals[m] / total_pre_split if total_pre_split else 0
    total = member_totals[m] + tax * share + tip * share
    member_final_totals[m] = total

st.markdown("### Final Amount Per Person")
member_final_totals_df = pd.DataFrame([
    {"Member": m, "Total Owed": f"${member_final_totals[m]:,.2f}"}
    for m in st.session_state.members
])
st.dataframe(member_final_totals_df, hide_index=True, use_container_width=True)

st.markdown("""
    <div style="
        margin-top: 3rem;
        background-color: #007aff;
        color: white;
        text-align: center;
        padding: 1.2rem;
        font-size: 1.5rem;
        font-weight: 600;
        border-radius: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
    " onmouseover="this.style.backgroundColor='#005bb5'" onmouseout="this.style.backgroundColor='#007aff'">
        Send Requests
    </div>
""", unsafe_allow_html=True)