"""
Classification Adjuster UI Component

Provides a Streamlit interface for users to review and adjust expense
classifications before running financial simulations.

Allows users to:
- View all detected expense categories
- See auto-detected classification (mandatory/negotiable/optional)
- Override classifications for specific items
- Specify if expenses can be paid by credit card (for Phase 2 planning)
- Bulk adjust related categories
- Export adjusted classifications
"""

from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


def display_classification_adjuster(
    transactions,
) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
    """
    Display an interactive classification adjustment UI.

    Args:
        transactions: Either a pandas DataFrame or a list of transaction dicts
                     with 'description' and 'category' keys.

    Returns:
        Tuple of:
        - classification_map: Dict mapping category -> classification type
        - adjusted_df: DataFrame with all transactions and their final classifications
    """

    # Convert to DataFrame if needed
    if isinstance(transactions, pd.DataFrame):
        df = transactions.copy()
    elif isinstance(transactions, list):
        df = pd.DataFrame(transactions)
    else:
        st.warning("Invalid transactions data type.")
        return {}, pd.DataFrame()

    if df.empty or len(df) == 0:
        st.warning("No transactions to classify.")
        return {}, pd.DataFrame()

    # Initialize session state variables for custom and deleted expenses
    # These persist across step navigation (important!)
    if "custom_expenses" not in st.session_state:
        st.session_state.custom_expenses = {}
    if "deleted_expenses" not in st.session_state:
        st.session_state.deleted_expenses = []
    if "adjusted_classifications" not in st.session_state:
        st.session_state.adjusted_classifications = {}
    if "adjusted_cc_eligibility" not in st.session_state:
        st.session_state.adjusted_cc_eligibility = {}
    if "adjusted_amounts" not in st.session_state:
        st.session_state.adjusted_amounts = {}

    # Group by description to aggregate
    # Build agg dict based on available columns
    agg_dict = {
        "amount": ["sum", "count", "mean"],
    }

    # Add category if it exists (for proper classification)
    if "category" in df.columns:
        agg_dict["category"] = "first"

    # Only add payable_by_credit if it exists
    if "payable_by_credit" in df.columns:
        agg_dict["payable_by_credit"] = "first"

    category_summary = df.groupby("description").agg(agg_dict).reset_index()

    # Handle column names based on what was aggregated
    if "category" in df.columns and "payable_by_credit" in df.columns:
        category_summary.columns = [
            "description",
            "total_amount",
            "transaction_count",
            "monthly_avg_amount",
            "auto_classification",
            "auto_cc_eligible",
        ]
    elif "category" in df.columns:
        category_summary.columns = [
            "description",
            "total_amount",
            "transaction_count",
            "monthly_avg_amount",
            "auto_classification",
        ]
        category_summary["auto_cc_eligible"] = True  # Default if not present
    elif "payable_by_credit" in df.columns:
        category_summary.columns = [
            "description",
            "total_amount",
            "transaction_count",
            "monthly_avg_amount",
            "auto_cc_eligible",
        ]
        category_summary["auto_classification"] = "negotiable"  # Default
    else:
        category_summary.columns = [
            "description",
            "total_amount",
            "transaction_count",
            "monthly_avg_amount",
        ]
        category_summary["auto_classification"] = "negotiable"  # Default
        category_summary["auto_cc_eligible"] = True  # Default if not present

    # Initialize adjusted amounts from session state or use auto-calculated monthly average
    if "adjusted_amounts" not in st.session_state:
        st.session_state.adjusted_amounts = {}

    category_summary = category_summary.sort_values("monthly_avg_amount", ascending=False)

    # PRE-POPULATE classifications from re-uploaded file (if they exist)
    if "classification" in df.columns:
        # If user is re-uploading a previously-exported file with classifications
        # Pre-populate the adjusted_classifications from that data
        for desc, group_df in df.groupby("description"):
            # Get the first (should all be the same) classification value
            saved_classification = group_df["classification"].iloc[0]
            if saved_classification and saved_classification.lower() in ["mandatory", "negotiable", "optional", "prepaid"]:
                st.session_state.adjusted_classifications[desc] = saved_classification.lower()

    # Display header
    st.subheader("[PROFILE] Expense Classification Review")
    st.markdown(
        """
    Review the auto-detected classifications below. You can override any that don't match your situation.

    **Classification Types:**
    - **Mandatory** [HIGH]: Essential for survival (rent, utilities, basic food, insurance, minimum debt payments)
    - **Negotiable** 🟠: Important but flexible (subscriptions, some dining out, non-critical insurance)
    - **Optional** 🔵: Pure discretionary (entertainment, luxury shopping, premium services)
    - **Prepaid** [CREDIT]: Already paid in advance (will zero out monthly cost - useful for insurance, services, etc.)

    **Credit Card Eligibility:**
    For Phase 2 planning (retirement phase), expenses marked as credit card eligible can be charged to help preserve cash.
    """
    )

    # Summary stats - use simple display instead of metrics to avoid sprintf issues
    col1, col2, col3, col4, col5 = st.columns(5)

    total_cats = len(category_summary)
    mandatory_count = int((category_summary["auto_classification"] == "mandatory").sum())
    negotiable_count = int((category_summary["auto_classification"] == "negotiable").sum())
    optional_count = int((category_summary["auto_classification"] == "optional").sum())
    cc_eligible = int(category_summary["auto_cc_eligible"].sum())
    total_monthly_avg = category_summary["monthly_avg_amount"].sum()

    with col1:
        st.write(f"**{total_cats}**  \nCategories")

    with col2:
        st.write(f"**${total_monthly_avg:,.0f}**  \nMonthly Avg")

    with col3:
        st.write(f"**{mandatory_count}**  \nMandatory")

    with col4:
        st.write(f"**{negotiable_count}**  \nNegotiable")

    with col5:
        st.write(f"**{optional_count}**  \nOptional")

    # Bulk classification options
    st.markdown("---")
    st.write("**Quick Actions:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("[YES] Accept All Auto-Classifications"):
            st.session_state.classifications_reviewed = True
            st.success("[YES] Accepted all auto-classifications!")

    with col2:
        if st.button("[RESET] Reset to Auto-Detect"):
            st.session_state.adjusted_classifications = {}
            st.session_state.adjusted_cc_eligibility = {}
            st.session_state.adjusted_amounts = {}
            st.info("Reset to auto-detected values.")
            st.rerun()

    with col3:
        if st.button("[STATS] Export as CSV"):
            export_df = category_summary[
                [
                    "description",
                    "total_amount",
                    "transaction_count",
                    "auto_classification",
                    "auto_cc_eligible",
                ]
            ].copy()
            export_df.columns = [
                "Description",
                "Total Amount",
                "Count",
                "Classification",
                "Credit Card Eligible",
            ]
            # Ensure all values are properly escaped
            export_df["Description"] = export_df["Description"].astype(str).str.replace("%", "%%")
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="expense_classifications.csv",
                mime="text/csv",
            )

    # Interactive classification table
    st.markdown("---")
    st.write("**Manage Expenses:**")

    # Section: Add Custom Expense
    with st.expander("➕ Add Custom Expense", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            custom_name = st.text_input(
                "Expense Name", placeholder="e.g., Pacific Life Prepaid", key="custom_expense_name"
            )
        with col2:
            custom_amount = st.number_input("Monthly Amount ($)", min_value=0.0, step=10.0, key="custom_expense_amount")
        with col3:
            custom_classification = st.selectbox(
                "Classification", ["mandatory", "negotiable", "optional", "prepaid"], key="custom_expense_class"
            )
        with col4:
            custom_cc = st.checkbox("Credit Card?", key="custom_expense_cc")

        if st.button("Add Expense", key="add_custom_expense"):
            if custom_name and custom_amount > 0:
                # Add to session state
                if "custom_expenses" not in st.session_state:
                    st.session_state.custom_expenses = {}
                st.session_state.custom_expenses[custom_name] = {
                    "amount": custom_amount,
                    "classification": custom_classification,
                    "cc_eligible": custom_cc,
                }
                st.success(f"✓ Added '{custom_name}' (${custom_amount:,.0f})")
                st.rerun()
            else:
                st.error("Please enter a name and amount")

    # Section: Restore Deleted Expenses
    if "deleted_expenses" in st.session_state and len(st.session_state.deleted_expenses) > 0:
        with st.expander("[RESET] Restore Deleted Expenses", expanded=True):
            st.write(f"**{len(st.session_state.deleted_expenses)} expense(s) marked for deletion:**")
            col1, col2, col3 = st.columns([3, 1, 1])
            for expired in st.session_state.deleted_expenses:
                with col1:
                    st.text(expired)
                with col2:
                    if st.button("Restore", key=f"restore_{expired}"):
                        st.session_state.deleted_expenses.remove(expired)
                        st.success(f"Restored '{expired}'")
                        st.rerun()
                with col3:
                    pass  # Spacer

    # Add custom expenses to the category summary
    if "custom_expenses" not in st.session_state:
        st.session_state.custom_expenses = {}

    for custom_name, custom_data in st.session_state.custom_expenses.items():
        if custom_name not in category_summary["description"].values:
            new_row = pd.DataFrame(
                {
                    "description": [custom_name],
                    "total_amount": [custom_data["amount"]],
                    "transaction_count": [1],
                    "monthly_avg_amount": [custom_data["amount"]],
                    "auto_classification": [custom_data["classification"]],
                    "auto_cc_eligible": [custom_data["cc_eligible"]],
                }
            )
            category_summary = pd.concat([category_summary, new_row], ignore_index=True)

    st.write("**Adjust Classifications & Credit Card Eligibility Below:**")

    # Session state already initialized at function start - no need to re-check

    # Create columns for the table header - 7 columns (added Delete column)
    col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.3, 1.5, 1.5, 1.2, 0.8, 0.6])

    with col1:
        st.write("**Description**")
    with col2:
        st.write("**Monthly Avg**")
    with col3:
        st.write("**Classification**")
    with col4:
        st.write("**Adjusted Amt**")
    with col5:
        st.write("**CC Eligible?**")
    with col6:
        st.write("**Status**")
    with col7:
        st.write("**Action**")

    # Render each category as an editable row
    adjustments = {}
    cc_adjustments = {}
    amount_adjustments = {}
    deleted_descriptions = []

    for idx, row in category_summary.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.3, 1.5, 1.5, 1.2, 0.8, 0.6])

        description = str(row["description"]).replace("%", "%%")  # Escape % signs
        auto_class = row["auto_classification"]
        auto_cc = row["auto_cc_eligible"]
        monthly_avg = float(row["monthly_avg_amount"])

        # Use description as key (stable across reruns, not row index)
        stable_key = f"exp_{description.replace(' ', '_').replace('/', '_')}"

        with col1:
            display_text = description[:35] + "..." if len(description) > 35 else description
            st.text(display_text)

        with col2:
            st.text(f"${monthly_avg:,.0f}")

        with col3:
            # Dropdown to override classification
            current_override = st.session_state.adjusted_classifications.get(description, auto_class)

            # Build options list - include prepaid option
            options = ["mandatory", "negotiable", "optional", "prepaid"]
            try:
                index = options.index(current_override)
            except ValueError:
                # If current_override not in options, default to first option
                index = 0
                current_override = options[0]

            new_classification = st.selectbox(
                label="Classification",
                options=options,
                index=index,
                key=f"{stable_key}_classification",
                label_visibility="collapsed",
            )

            if new_classification != auto_class:
                st.session_state.adjusted_classifications[description] = new_classification
                adjustments[description] = new_classification
                # Note: Prepaid expenses are tracked separately (already paid in advance)
                # Don't zero them out - keep them for budget planning
            elif description in st.session_state.adjusted_classifications:
                adjustments[description] = st.session_state.adjusted_classifications[description]
            else:
                adjustments[description] = auto_class

        with col4:
            # Number input to adjust amount (use absolute value since expenses are negative)
            current_amount = st.session_state.adjusted_amounts.get(description, abs(monthly_avg))

            new_amount = st.number_input(
                label="Adjusted Amount",
                value=float(current_amount),
                min_value=0.0,
                step=10.0,
                key=f"{stable_key}_amount",
                label_visibility="collapsed",
            )

            if new_amount != abs(monthly_avg):
                st.session_state.adjusted_amounts[description] = new_amount
                amount_adjustments[description] = new_amount
            elif description in st.session_state.adjusted_amounts:
                amount_adjustments[description] = st.session_state.adjusted_amounts[description]
            else:
                amount_adjustments[description] = monthly_avg

        with col5:
            # Toggle for credit card eligibility
            current_cc = st.session_state.adjusted_cc_eligibility.get(description, auto_cc)

            new_cc = st.checkbox(
                "CC",
                value=current_cc,
                key=f"{stable_key}_cc",
            )

            if new_cc != auto_cc:
                st.session_state.adjusted_cc_eligibility[description] = new_cc
                cc_adjustments[description] = new_cc
            elif description in st.session_state.adjusted_cc_eligibility:
                cc_adjustments[description] = st.session_state.adjusted_cc_eligibility[description]
            else:
                cc_adjustments[description] = auto_cc

        with col6:
            # Show status indicator
            changed_class = new_classification != auto_class
            changed_amount = new_amount != monthly_avg
            changed_cc = new_cc != auto_cc

            if changed_class or changed_amount or changed_cc:
                st.markdown("✏️")
            else:
                st.markdown("✓")

        with col7:
            # Delete button
            if st.button("🗑️", key=f"{stable_key}_delete", help="Delete this expense"):
                deleted_descriptions.append(description)
                if "deleted_expenses" not in st.session_state:
                    st.session_state.deleted_expenses = []
                st.session_state.deleted_expenses.append(description)
                st.info(f"Marked '{description}' for deletion")
                st.rerun()

    # Filter out deleted expenses
    if "deleted_expenses" not in st.session_state:
        st.session_state.deleted_expenses = []

    active_descriptions = [
        row["description"]
        for _, row in category_summary.iterrows()
        if row["description"] not in st.session_state.deleted_expenses
    ]

    # Apply adjustments to original data
    final_classifications = {
        row["description"]: adjustments.get(row["description"], row["auto_classification"])
        for _, row in category_summary.iterrows()
        if row["description"] not in st.session_state.deleted_expenses
    }

    final_amounts = {
        row["description"]: amount_adjustments.get(row["description"], row["monthly_avg_amount"])
        for _, row in category_summary.iterrows()
        if row["description"] not in st.session_state.deleted_expenses
    }

    final_cc_eligibility = {
        row["description"]: cc_adjustments.get(row["description"], row["auto_cc_eligible"])
        for _, row in category_summary.iterrows()
        if row["description"] not in st.session_state.deleted_expenses
    }

    # Map back to all transactions (exclude deleted items by mapping to None)
    df["adjusted_category"] = df["description"].map(final_classifications)
    df["adjusted_payable_by_credit"] = df["description"].map(final_cc_eligibility)
    df["adjusted_monthly_amount"] = df["description"].map(final_amounts)

    # Filter out any rows with deleted descriptions
    df = df[~df["description"].isin(st.session_state.deleted_expenses)]

    # Summary of changes
    st.markdown("---")
    deleted_count = len(st.session_state.deleted_expenses)
    custom_count = len(st.session_state.get("custom_expenses", {}))

    class_changes = sum(
        1
        for desc, new_class in adjustments.items()
        if new_class != category_summary[category_summary["description"] == desc]["auto_classification"].values[0]
    )
    cc_changes = sum(
        1
        for desc, new_cc in cc_adjustments.items()
        if new_cc != category_summary[category_summary["description"] == desc]["auto_cc_eligible"].values[0]
    )
    amount_changes = sum(
        1
        for desc, new_amt in amount_adjustments.items()
        if new_amt != category_summary[category_summary["description"] == desc]["monthly_avg_amount"].values[0]
    )
    total_changes = class_changes + cc_changes + amount_changes

    if deleted_count > 0:
        st.warning(f"🗑️ Removed {deleted_count} expense(s). Click '[YES] Accept...' to confirm.", icon="[WARNING]")

    if custom_count > 0:
        st.info(f"➕ Added {custom_count} custom expense(s).")

    if total_changes > 0:
        st.info(
            f"ℹ️ You've adjusted {total_changes} settings ({class_changes} classifications, {amount_changes} amounts, {cc_changes} credit card eligibility)."
        )
    elif deleted_count == 0 and custom_count == 0:
        st.success("✓ Using all auto-detected values.")

    # Section: Merge Categories
    st.markdown("---")
    with st.expander("🔗 Merge Categories (Advanced)", expanded=False):
        st.write(
            "Combine similar expense categories into one line item (e.g., Phone + Mobile Insurance = Communications)"
        )

        active_expenses = list(final_classifications.keys())
        if len(active_expenses) > 1:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                primary_cat = st.selectbox("Primary Category (keep this name)", active_expenses, key="merge_primary")
            with col2:
                secondary_options = [e for e in active_expenses if e != primary_cat]
                merged_cats = st.multiselect("Merge these into Primary", secondary_options, key="merge_secondary")
            with col3:
                if st.button("Merge", key="do_merge"):
                    if merged_cats:
                        if "merged_categories" not in st.session_state:
                            st.session_state.merged_categories = {}
                        # Sum amounts from secondary to primary
                        primary_amount = final_amounts.get(primary_cat, 0)
                        for cat in merged_cats:
                            primary_amount += final_amounts.get(cat, 0)

                        # Update final amounts - set merged amounts to 0 and primary to sum
                        final_amounts[primary_cat] = primary_amount
                        for cat in merged_cats:
                            final_amounts[cat] = 0
                            final_classifications[cat] = None  # Mark for exclusion

                        st.session_state.merged_categories[primary_cat] = merged_cats
                        st.success(
                            f"✓ Merged {len(merged_cats)} categories into '{primary_cat}' (${primary_amount:,.0f}/mo)"
                        )
                        st.rerun()
        else:
            st.info("Need at least 2 active categories to merge")

    # Return the adjusted classifications and updated dataframe
    classification_map = {
        row["description"]: final_classifications[row["description"]]
        for _, row in category_summary.iterrows()
        if final_classifications.get(row["description"]) is not None  # Exclude merged categories
    }

    # Calculate breakdown by classification for Step 3 (Debt vs Savings)
    mandatory_total = sum(
        amount for desc, amount in final_amounts.items() if final_classifications.get(desc) == "mandatory"
    )
    negotiable_total = sum(
        amount for desc, amount in final_amounts.items() if final_classifications.get(desc) == "negotiable"
    )
    optional_total = sum(
        amount for desc, amount in final_amounts.items() if final_classifications.get(desc) == "optional"
    )
    prepaid_total = sum(
        amount for desc, amount in final_amounts.items() if final_classifications.get(desc) == "prepaid"
    )

    # Debug: Show what's being included/excluded
    with st.expander("[SEARCH] Debug: Expense Breakdown", expanded=False):
        st.write("**Final Amounts Dictionary:**")
        for desc, amt in final_amounts.items():
            class_type = final_classifications.get(desc, "NONE")
            included = "✓" if class_type in ["mandatory", "negotiable", "optional"] else "✗ Excluded"
            st.text(f"{included} {desc}: ${amt:,.0f} ({class_type})")

        st.write("**Summary:**")
        st.text(f"Mandatory: ${mandatory_total:,.0f}")
        st.text(f"Negotiable: ${negotiable_total:,.0f}")
        st.text(f"Optional: ${optional_total:,.0f}")
        st.text(f"Prepaid: ${prepaid_total:,.0f}")
        st.text(f"Total: ${mandatory_total + negotiable_total + optional_total + prepaid_total:,.0f}")

        if deleted_count > 0:
            st.write(f"**Deleted ({deleted_count}):**")
            for item in st.session_state.deleted_expenses:
                st.text(f"  - {item}")

        if "merged_categories" in st.session_state and st.session_state.merged_categories:
            st.write("**Merged:**")
            for primary, secondary_list in st.session_state.merged_categories.items():
                st.text(f"  {primary} ← {', '.join(secondary_list)}")

    # Calculate CC-payable breakdown for THEMIS Decision Engine
    cc_payable_mandatory = sum(
        amount
        for desc, amount in final_amounts.items()
        if final_classifications.get(desc) == "mandatory" and final_cc_eligibility.get(desc, False)
    )
    cc_payable_negotiable = sum(
        amount
        for desc, amount in final_amounts.items()
        if final_classifications.get(desc) == "negotiable" and final_cc_eligibility.get(desc, False)
    )
    cc_payable_optional = sum(
        amount
        for desc, amount in final_amounts.items()
        if final_classifications.get(desc) == "optional" and final_cc_eligibility.get(desc, False)
    )

    cash_only_mandatory = mandatory_total - cc_payable_mandatory
    cash_only_negotiable = negotiable_total - cc_payable_negotiable
    cash_only_optional = optional_total - cc_payable_optional

    # Save breakdown to session state for use in Step 3 (THEMIS)
    st.session_state.csv_mandatory_expenses = mandatory_total
    st.session_state.csv_negotiable_expenses = negotiable_total
    st.session_state.csv_optional_expenses = optional_total
    st.session_state.csv_prepaid_expenses = prepaid_total
    st.session_state.csv_classification_map = final_classifications
    st.session_state.final_amounts = final_amounts  # Save amounts for Step 8 prepaid tracker

    # Save CC-payable breakdown for THEMIS Decision Engine
    st.session_state.cc_payable_expenses = {
        "mandatory": cc_payable_mandatory,
        "negotiable": cc_payable_negotiable,
        "optional": cc_payable_optional,
        "total": cc_payable_mandatory + cc_payable_negotiable + cc_payable_optional,
    }

    # Save cash-only breakdown for THEMIS Decision Engine
    st.session_state.cash_only_expenses = {
        "mandatory": cash_only_mandatory,
        "negotiable": cash_only_negotiable,
        "optional": cash_only_optional,
        "total": cash_only_mandatory + cash_only_negotiable + cash_only_optional,
    }

    # Save the full CC eligibility map for reference
    st.session_state.adjusted_cc_eligibility_final = final_cc_eligibility

    return classification_map, df


def summarize_by_classification(df: pd.DataFrame) -> Dict[str, float]:
    """
    Summarize total expenses by classification type.

    Args:
        df: DataFrame with 'amount' and 'adjusted_category' (or 'category') columns.

    Returns:
        Dict with totals for each classification type.
    """

    col_to_use = "adjusted_category" if "adjusted_category" in df.columns else "category"

    summary = {}
    for classification_type in ["mandatory", "negotiable", "optional"]:
        total = df[df[col_to_use] == classification_type]["amount"].sum()
        summary[classification_type] = total

    return summary
