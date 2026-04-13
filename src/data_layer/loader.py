"""
Data loading and cleaning module for Project Atlas.

This module handles reading and processing user-uploaded CSV files (transaction
histories, expense reports, etc.) and performing initial data cleaning to ensure
consistency and quality for downstream model processing.
"""

import logging
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class DataCleaningError(Exception):
    """Custom exception for data cleaning failures."""


def load_and_clean_csv(uploaded_file, expected_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load and clean a CSV file from a Streamlit UploadedFile object.

    This function:
    1. Reads the CSV into a pandas DataFrame
    2. Standardizes column names (lowercase, underscores, removes extra spaces)
    3. Performs data type validation
    4. Handles missing values
    5. Validates required columns exist

    Args:
        uploaded_file: Streamlit UploadedFile object from st.file_uploader().
        expected_columns (Optional[List[str]]): List of column names that MUST
            exist in the CSV (after standardization). If None, only basic
            cleaning is performed. Example: ['date', 'description', 'amount']

    Returns:
        pd.DataFrame: Cleaned DataFrame ready for processing.

    Raises:
        DataCleaningError: If the file format is invalid, required columns
            are missing, or data cleaning fails.

    Example:
        >>> import streamlit as st
        >>> uploaded_file = st.file_uploader("Upload CSV")
        >>> df = load_and_clean_csv(
        ...     uploaded_file,
        ...     expected_columns=['date', 'description', 'amount']
        ... )
    """

    if uploaded_file is None:
        raise DataCleaningError("No file provided.")

    try:
        # Read CSV into DataFrame
        # Handle both text and binary file modes
        if hasattr(uploaded_file, "read"):
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            df = pd.read_csv(StringIO(content))
        else:
            raise DataCleaningError("Invalid file object. Expected Streamlit UploadedFile.")
    except pd.errors.ParserError as e:
        raise DataCleaningError(f"Failed to parse CSV file. Check file format: {str(e)}")
    except UnicodeDecodeError as e:
        raise DataCleaningError(f"File encoding error. Please use UTF-8 encoded CSV: {str(e)}")

    if df.empty:
        raise DataCleaningError("CSV file is empty.")

    # Standardize column names
    df.columns = _standardize_column_names(df.columns)

    logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns.")
    logger.info(f"Columns: {list(df.columns)}")

    # Validate expected columns if provided
    if expected_columns:
        expected_columns = [_standardize_name(col) for col in expected_columns]
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            raise DataCleaningError(f"Missing required columns: {missing_columns}. " f"Found: {set(df.columns)}")

    # Remove completely empty rows and columns
    df = df.dropna(how="all")  # Remove rows that are all NaN
    df = df.dropna(axis=1, how="all")  # Remove columns that are all NaN

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()

    logger.info("Data cleaning completed successfully.")

    return df


def clean_transaction_csv(uploaded_file) -> pd.DataFrame:
    """
    Flexible CSV loader for transaction AND budget data.

    Accepts:
    - Bank transaction exports (date, description, amount)
    - YNAB budget exports (month, category, assigned/activity/available)
    - Generic expense data with flexible column names

    Auto-classifies expenses into: mandatory, negotiable, optional

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        pd.DataFrame: Standardized with columns [date, description, amount, category]

    Raises:
        DataCleaningError: If cannot identify required data.
    """

    # Load the CSV
    df = load_and_clean_csv(uploaded_file)
    column_lower = {col.lower(): col for col in df.columns}

    # Detect format: Transaction vs Budget/YNAB
    is_ynab = _detect_ynab_format(df.columns)

    if is_ynab:
        return _process_ynab_budget(df, column_lower)
    else:
        return _process_transactions(df, column_lower)


def _sanitize_text(text: str) -> str:
    """
    Sanitize text to prevent sprintf formatting issues in Streamlit.

    Removes or escapes special characters that could cause issues with
    sprintf-style formatting in the UI.

    Args:
        text: Text to sanitize.

    Returns:
        Sanitized text safe for UI display.
    """
    if not isinstance(text, str):
        text = str(text)

    # Replace problematic characters
    # % can cause sprintf issues
    text = text.replace("%", "pct")

    return text.strip()


def _detect_ynab_format(columns) -> bool:
    """Check if CSV looks like YNAB budget export."""
    col_lower = [c.lower() for c in columns]
    ynab_indicators = ["category", "assigned", "available", "activity"]
    return sum(1 for ind in ynab_indicators if ind in col_lower) >= 2


def _determine_credit_card_eligibility(text: str) -> bool:
    """
    Determine if an expense can be paid by credit card (vs. cash-only).

    Most expenses can be paid by credit card, but some require cash or specific payment methods:
    - Cash-only: Cash withdrawals, certain government payments
    - Must use specific payment method: Mortgage/rent (often requires ACH), utilities (often auto-pay)

    For Phase 2 planning, users can allocate certain expenses to credit card during
    retirement gap when income is lower.

    Returns: True if can use credit card, False if cash-only
    """

    text_lower = text.lower()

    # Cash-only or must be paid directly (not by credit card)
    cash_only_keywords = [
        "atm",
        "cash withdrawal",
        "cash advance",
        "check",
        "wire transfer",
        "mortgage payment",
        "rent payment",
        "property tax",
        "child support",
    ]

    # These CAN technically be charged, but usually auto-deducted from bank account
    # User can decide to put on credit if needed for cash flow
    # (Note: reserved for future cash flow optimization logic)

    # Check if it's strictly cash-only
    for keyword in cash_only_keywords:
        if keyword in text_lower:
            return False

    # Default: Can be paid by credit card
    return True


def _process_ynab_budget(df: pd.DataFrame, column_lower: Dict) -> pd.DataFrame:
    """
    Process YNAB budget CSV format.
    Converts budget categories to monthly expense entries.

    IMPORTANT: Excludes Savings and Hidden Categories (these are not expenses).
    Uses "Activity" column (actual spending) rather than "Assigned" (budget).
    """

    # Find relevant columns
    # month_col is reserved for future date-based processing
    category_col = None
    for variant in ["category", "category_group", "category_groupcategory"]:
        if variant in column_lower:
            category_col = column_lower[variant]
            break

    # Try to use "Activity" (actual spending) first, fallback to "Assigned" (budget)
    amount_col = None
    for variant in ["activity", "assigned", "available"]:
        if variant in column_lower:
            amount_col = column_lower[variant]
            break

    if not category_col or not amount_col:
        raise DataCleaningError(
            f"YNAB format detected but missing category or amount column. " f"Found: {list(df.columns)}"
        )

    # Convert to transaction format
    rows = []
    for _, row in df.iterrows():
        category_name = str(row[category_col]).strip()

        # SKIP non-expense categories - these are not living expenses
        category_lower = category_name.lower()
        skip_keywords = [
            "savings:",  # Savings goals
            "hidden",  # Hidden/tracking categories
            "credit card payment",  # Credit card transfers
            "credit card:",  # Credit card accounts
            "visa",  # Credit card names (Visa, Amex, etc.)
            "mastercard",
            "amex",
            "capital one",
            "fidelity",  # Investment/credit services
            "investment",  # Investment accounts/transfers
            "retirement",  # Retirement savings
            "401k",
            "ira",
            "debt consolidation",  # Debt transfers
            "debt payment",  # Debt transfers
            "loan payment",  # Loan transfers (not the actual expense)
            "goal tracker:",  # Goal tracking
            "transfer",  # Generic transfers
        ]

        if any(keyword in category_lower for keyword in skip_keywords):
            continue

        amount = _clean_amount_column(row[amount_col])

        if amount == 0:
            continue

        # Auto-classify based on category name
        expense_category = _classify_category(category_name)

        # Determine if payable by credit card
        payable_by_credit = _determine_credit_card_eligibility(category_name)

        rows.append(
            {
                "date": pd.Timestamp.now(),  # Use current date for budget items
                "description": _sanitize_text(category_name),
                "amount": abs(amount),  # Budget amounts are typically positive
                "category": expense_category,
                "payable_by_credit": payable_by_credit,
            }
        )

    if not rows:
        raise DataCleaningError("No non-zero budget items found in CSV (after excluding Savings and Hidden Categories)")

    df_clean = pd.DataFrame(rows)

    logger.info(f"Processed YNAB budget: {len(df_clean)} categories auto-classified (Savings/Hidden excluded)")

    return df_clean


def _process_transactions(df: pd.DataFrame, column_lower: Dict) -> pd.DataFrame:
    """
    Process traditional bank transaction CSV format.

    For YNAB Register exports: Filters out non-expense categories (Savings, Debt,
    Transfers, Investment, Retirement, etc.) using the Category/Category Group columns.
    """

    # Find date column
    date_col = None
    for variant in ["date", "month", "date_posted", "transaction_date", "posted_date"]:
        if variant in column_lower:
            date_col = column_lower[variant]
            break

    # Find description column
    desc_col = None
    for variant in ["description", "payee", "memo", "note", "merchant"]:
        if variant in column_lower:
            desc_col = column_lower[variant]
            break

    # Find amount column (prefer outflow for YNAB Register exports)
    amount_col = None
    for variant in ["outflow", "inflow", "amount", "value", "transaction_amount"]:
        if variant in column_lower:
            amount_col = column_lower[variant]
            break

    # Look for category/category_group columns (for YNAB filtering)
    category_col = None
    for variant in ["category", "category_group", "category group/category", "category_groupcategory"]:
        if variant in column_lower:
            category_col = column_lower[variant]
            break

    # Validate required columns
    missing = []
    if not date_col:
        missing.append("date")
    if not desc_col:
        missing.append("description")
    if not amount_col:
        missing.append("amount")

    if missing:
        raise DataCleaningError(
            f"Transaction format requires: {', '.join(missing)}. " f"Found columns: {list(df.columns)}"
        )

    # Filter out non-expense categories if category column exists
    df_filtered = df.copy()
    if category_col:
        skip_keywords = [
            "savings:",  # Savings goals
            "hidden",  # Hidden/tracking categories
            "credit card payment",  # Credit card transfers
            "credit card:",  # Credit card accounts
            "visa",  # Credit card names
            "mastercard",
            "amex",
            "capital one",
            "fidelity",  # Investment/credit services
            "investment",  # Investment accounts
            "retirement",  # Retirement savings
            "401k",
            "ira",
            "debt:",  # Debt accounts (loans, CCs) - these are transfers, not expenses
            "debt payment",
            "goal tracker:",  # Goal tracking
            "inflow:",  # Income - not an expense (in YNAB Register exports)
            "ready to assign",  # Unassigned income
            "transfer",  # Generic transfers between accounts
        ]

        def should_skip_category(cat_text):
            if pd.isna(cat_text):
                return False  # Keep uncategorized
            cat_lower = str(cat_text).lower()
            return any(keyword in cat_lower for keyword in skip_keywords)

        df_filtered = df[~df[category_col].apply(should_skip_category)].copy()
        logger.info(f"Filtered categories: kept {len(df_filtered)} of {len(df)} rows")

    # Create standardized dataframe
    df_clean = pd.DataFrame(
        {
            "date": df_filtered[date_col],
            "description": df_filtered[desc_col].astype(str).apply(_sanitize_text),
            "amount": df_filtered[amount_col],
        }
    )

    # Preserve classification column if it exists (from previously-exported file)
    classification_col = None
    for variant in ["classification", "class"]:
        if variant in column_lower:
            classification_col = column_lower[variant]
            break
    
    if classification_col:
        df_clean["classification"] = df_filtered[classification_col]

    # Convert date
    try:
        df_clean["date"] = pd.to_datetime(df_clean["date"], format="mixed", infer_datetime_format=True)
    except Exception as e:
        raise DataCleaningError(f"Failed to parse dates: {str(e)}")

    # Convert amount
    df_clean["amount"] = df_clean["amount"].apply(_clean_amount_column)
    df_clean = df_clean[df_clean["amount"] != 0]

    # Auto-classify by description
    df_clean["category"] = df_clean["description"].apply(_classify_category)

    # Determine credit card eligibility
    df_clean["payable_by_credit"] = df_clean["description"].apply(_determine_credit_card_eligibility)

    # Sort by date
    df_clean = df_clean.sort_values("date").reset_index(drop=True)

    logger.info(f"Processed {len(df_clean)} transactions from {df_clean['date'].min()} to {df_clean['date'].max()}")

    return df_clean


def _classify_category(text: str) -> str:
    """
    Auto-classify expense by name/description into three tiers:
    - 'mandatory': Essential for survival/legal obligations (housing, utilities, debt, healthcare, food)
    - 'negotiable': Important but flexible (subscriptions, hobbies, insurance add-ons)
    - 'optional': Luxury/discretionary (dining out, entertainment, shopping, travel)

    Returns: 'mandatory', 'negotiable', or 'optional'

    Note: User can override these classifications in the UI for their specific situation.
    """

    text_lower = text.lower()

    # === MANDATORY: Non-negotiable for survival ===
    # Housing
    mandatory_keywords = [
        "rent",
        "mortgage",
        "property tax",
        "homeowner",
        "property management",
        "hoa",
        "home repair",
        "maintenance",
    ]

    # Utilities & Essential Services
    mandatory_keywords.extend(
        [
            "electricity",
            "electric",
            "power",
            "gas bill",
            "natural gas",
            "propane",
            "water",
            "sewer",
            "waste water",
            "trash",
            "garbage",
            "recycling",
            "internet",
            "broadband",
            "isp",
            "phone",
            "mobile",
            "cell phone",
            "wireless",
            "landline",
        ]
    )

    # Transportation (Essential)
    mandatory_keywords.extend(
        [
            "car payment",
            "auto loan",
            "vehicle loan",
            "car insurance",
            "auto insurance",
            "vehicle insurance",
            "fuel",
            "gas station",
            "pump",
            "car maintenance",
            "oil change",
            "tire",
            "parking meter",
            "parking fee",
            "registration",
            "vehicle registration",
            "license plate",
            "inspection",
            "emission",
        ]
    )

    # Food (Basic)
    mandatory_keywords.extend(
        [
            "groceries",
            "grocery",
            "supermarket",
            "farmers market",
            "produce",
            "breakfast",
            "lunch",
            "dinner",  # Basic meals at home
        ]
    )

    # Healthcare & Insurance
    mandatory_keywords.extend(
        [
            "insurance",
            "medical insurance",
            "health insurance",
            "tricare",
            "va health",
            "copay",
            "co-pay",
            "prescription",
            "pharmacy",
            "medication",
            "doctor",
            "dentist",
            "dental",
            "physician",
            "hospital",
            "emergency room",
            "er",
            "therapy",
            "mental health",
        ]
    )

    # Debt Payments
    mandatory_keywords.extend(
        [
            "debt payment",
            "debt repayment",
            "credit card payment",
            "credit card bill",
            "loan payment",
            "student loan",
            "mortgage payment",
        ]
    )

    # Childcare & Support (if applicable)
    mandatory_keywords.extend(
        [
            "childcare",
            "daycare",
            "babysitter",
            "child support",
            "alimony",
            "nanny",
            "preschool",
        ]
    )

    # === NEGOTIABLE: Important but flexible ===
    negotiable_keywords = [
        # Subscriptions (can be cut)
        "subscription",
        "subscriptions",
        "membership",
        "annual fee",
        "premium",
        "plus",
        # Insurance add-ons
        "life insurance",
        "disability insurance",
        "umbrella insurance",
        # Savings/Goals (good to keep but flexible timing)
        "savings",
        "savings account",
        "emergency fund",
        "retirement",
        "401k",
        "ira",
        "investment",
        "brokerage",
        # Home/Vehicle upgrades
        "home improvement",
        "upgrade",
        "renovation",
        "vehicle upgrade",
        "car upgrade",
        # Hobbies (moderate)
        "hobby",
        "crafts",
        "diy",
        # Education
        "education",
        "course",
        "training",
        "tuition",
        "class",
        "lessons",
        "certification",
        # Pet care (essential if you have pets, but amount is flexible)
        "pet food",
        "pet care",
        "veterinarian",
        "vet",
        "dog",
        "cat",
        "animal",
        # Clothing (moderate shopping)
        "clothing",
        "clothes",
        "apparel",
        "shoes",
        "work clothes",
        "uniform",
    ]

    # === OPTIONAL: Pure discretionary ===
    optional_keywords = [
        # Dining Out & Entertainment
        "restaurant",
        "dining out",
        "bar",
        "brewery",
        "wine bar",
        "cafe",
        "coffee shop",
        "café",
        "fast food",
        "food delivery",
        "doordash",
        "ubereats",
        "takeout",
        "delivery",
        # Streaming/Media/Entertainment
        "streaming",
        "netflix",
        "hulu",
        "disney+",
        "hbo",
        "amazon prime",
        "movie",
        "theater",
        "cinema",
        "spotify",
        "music",
        "apple music",
        "pandora",
        "gaming",
        "game",
        "playstation",
        "xbox",
        "steam",
        "entertainment",
        "recreation",
        # Shopping/Retail (non-essential)
        "shopping",
        "retail",
        "mall",
        "fashion",
        "boutique",
        "brand",
        "amazon",
        "ebay",
        "target",
        "walmart",
        "luxury",
        "designer",
        "high-end",
        # Travel & Vacation
        "vacation",
        "travel",
        "trip",
        "hotel",
        "airbnb",
        "resort",
        "flight",
        "airline",
        "cruise",
        "sightseeing",
        "tour",
        # Sports & Fitness (premium)
        "gym",
        "fitness",
        "personal trainer",
        "yoga",
        "pilates",
        "crossfit",
        "sports equipment",
        "sports",
        "golf",
        "skiing",
        "cycling",
        "running club",
        # Beauty & Personal Care (premium)
        "salon",
        "spa",
        "massage",
        "haircut",
        "hair",
        "beauty",
        "cosmetics",
        "makeup",
        "nails",
        "manicure",
        "pedicure",
        # Gifts & Events
        "gift",
        "gifts",
        "birthday",
        "anniversary",
        "holiday",
        "christmas",
        # Furniture & Decor
        "furniture",
        "decor",
        "decoration",
        "appliance",
        # Miscellaneous luxury
        "luxury",
        "premium",
        "exclusive",
    ]

    # Check keywords with priority: optional > negotiable > mandatory
    # (Check specific before generic)

    for keyword in optional_keywords:
        if keyword in text_lower:
            return "optional"

    for keyword in negotiable_keywords:
        if keyword in text_lower:
            return "negotiable"

    for keyword in mandatory_keywords:
        if keyword in text_lower:
            return "mandatory"

    # Default: negotiable (can be cut if needed, but not pure discretionary)
    return "negotiable"


def _standardize_column_names(columns) -> List[str]:
    """
    Convert column names to standardized format.

    Converts to lowercase, replaces spaces with underscores, removes
    special characters, and trims whitespace.

    Args:
        columns: Iterable of column names (list or Index).

    Returns:
        List[str]: Standardized column names.

    Example:
        >>> _standardize_column_names(['Date', 'Transaction Amount', 'Desc.'])
        ['date', 'transaction_amount', 'desc']
    """
    return [_standardize_name(col) for col in columns]


def _standardize_name(name: str) -> str:
    """
    Standardize a single name string.

    Args:
        name (str): Name to standardize.

    Returns:
        str: Standardized name.
    """
    if not isinstance(name, str):
        name = str(name)

    # Lowercase
    name = name.lower()

    # Replace spaces with underscores
    name = name.replace(" ", "_")

    # Remove special characters except underscores
    name = "".join(c if c.isalnum() or c == "_" else "" for c in name)

    # Remove trailing/leading underscores
    name = name.strip("_")

    return name


def _clean_amount_column(value) -> float:
    """
    Convert a value (potentially with currency symbols/commas) to float.

    Args:
        value: The value to convert (str, int, or float).

    Returns:
        float: The numeric value.

    Raises:
        ValueError: If conversion fails.

    Example:
        >>> _clean_amount_column('$1,234.56')
        1234.56
        >>> _clean_amount_column('-$50.00')
        -50.0
    """
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    # Convert to string and clean
    value_str = str(value).strip()

    # Remove currency symbols, parentheses, spaces
    for char in ["$", "€", "£", "¥", ",", " ", "(", ")"]:
        value_str = value_str.replace(char, "")

    # Handle negative values indicated by parentheses
    if ")" in str(value):
        value_str = "-" + value_str.replace("-", "")

    try:
        return float(value_str)
    except ValueError:
        logger.warning(f"Could not parse amount: {value}. Using 0.0.")
        return 0.0


def validate_transaction_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that a transaction DataFrame has the correct structure.

    Args:
        df (pd.DataFrame): DataFrame to validate.

    Returns:
        bool: True if valid, raises DataCleaningError otherwise.

    Raises:
        DataCleaningError: If validation fails.
    """
    required_cols = {"date", "description", "amount", "category"}

    if not required_cols.issubset(set(df.columns)):
        raise DataCleaningError(
            f"Invalid transaction DataFrame. " f"Required columns: {required_cols}. Found: {set(df.columns)}"
        )

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise DataCleaningError("'date' column must be datetime type.")

    if not pd.api.types.is_numeric_dtype(df["amount"]):
        raise DataCleaningError("'amount' column must be numeric type.")

    if df["category"].isna().all():
        raise DataCleaningError("'category' column cannot be all null.")

    return True


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of the loaded data for user feedback.

    Args:
        df (pd.DataFrame): The data to summarize.

    Returns:
        Dict[str, Any]: Summary statistics.

    Example:
        >>> summary = get_data_summary(df)
        >>> print(f"Loaded {summary['row_count']} transactions")
    """
    summary = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }

    # Add numeric summaries if relevant columns exist
    if "amount" in df.columns and pd.api.types.is_numeric_dtype(df["amount"]):
        summary["amount_total"] = df["amount"].sum()
        summary["amount_mean"] = df["amount"].mean()
        summary["amount_min"] = df["amount"].min()
        summary["amount_max"] = df["amount"].max()

    return summary
