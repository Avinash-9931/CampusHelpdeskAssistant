"""
Admin User Management module for Campus Helpdesk Assistant.
Enforces RBAC (Admin only), single account creation, bulk CSV import,
role modifications, and status toggles with last-admin safeguards.
"""

import streamlit as st
from auth.guards import require_role, render_access_denied_view
from auth.service import (
    list_users,
    create_user,
    bulk_import_users_csv,
    toggle_user_status,
    update_user_role,
    reset_user_password_admin,
    count_active_admins
)
from ui.components import render_badge


def render_users_page():
    """Renders the Administrator User Management Console."""
    curr_user = st.session_state.get("auth_user")
    if not require_role(curr_user, "Admin"):
        render_access_denied_view("User Account Administration")
        return

    st.markdown("<h2>User Account Administration</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:var(--text-muted); font-size:13.5px; margin-top:-6px;'>"
        "Manage student and staff credentials, provision accounts, and perform bulk roster imports."
        "</p>",
        unsafe_allow_html=True
    )

    tab_users, tab_create, tab_bulk = st.tabs([
        "👥 Registered Accounts",
        "➕ Create Account",
        "📁 Bulk CSV Import"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: USER DIRECTORY
    # --------------------------------------------------------------------------
    with tab_users:
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_query = st.text_input("Filter users", placeholder="Search by name, ID, or email...")
        with col_s2:
            st.markdown(f"<div style='padding-top:28px; font-size:12px; font-weight:600; color:var(--accent);'>Active Admins: {count_active_admins()}</div>", unsafe_allow_html=True)

        users_list = list_users(search_query=search_query)

        if not users_list:
            st.info("No user accounts found matching your query.")
        else:
            st.markdown(f"<div style='font-size:12px; color:var(--text-muted); margin-bottom:10px;'>Displaying {len(users_list)} registered account(s)</div>", unsafe_allow_html=True)

            for u in users_list:
                with st.container(border=True):
                    c_info, c_role, c_status, c_actions = st.columns([2.2, 1, 1, 2.2])

                    with c_info:
                        st.markdown(f"**{u['name']}**")
                        st.markdown(f"<div style='font-size:12px; color:#64748B;'>ID: <code>{u['id']}</code> · {u['email']}</div>", unsafe_allow_html=True)
                        if u.get("last_login_at"):
                            st.markdown(f"<div style='font-size:11px; color:#94A3B8;'>Last login: {u['last_login_at']}</div>", unsafe_allow_html=True)

                    with c_role:
                        role_kind = "accent" if u["role"] == "Admin" else "secondary"
                        st.markdown(render_badge(u["role"], kind=role_kind), unsafe_allow_html=True)

                    with c_status:
                        stat_kind = "success" if u["status"] == "active" else "danger"
                        st.markdown(render_badge(u["status"].capitalize(), kind=stat_kind), unsafe_allow_html=True)

                    with c_actions:
                        act_c1, act_c2, act_c3 = st.columns(3)
                        with act_c1:
                            btn_label = "Disable" if u["status"] == "active" else "Enable"
                            if st.button(btn_label, key=f"btn_toggle_status_{u['id']}", use_container_width=True):
                                ok, msg = toggle_user_status(u["id"], actor_id=curr_user["id"])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                        with act_c2:
                            new_role = "Student" if u["role"] == "Admin" else "Admin"
                            role_btn_text = "To Student" if u["role"] == "Admin" else "To Admin"
                            if st.button(role_btn_text, key=f"btn_toggle_role_{u['id']}", use_container_width=True):
                                ok, msg = update_user_role(u["id"], new_role, actor_id=curr_user["id"])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                        with act_c3:
                            if st.button("Reset Pwd", key=f"btn_reset_pwd_{u['id']}", use_container_width=True):
                                ok, msg, temp_pwd = reset_user_password_admin(u["id"], actor_id=curr_user["id"])
                                if ok:
                                    st.info(f"Temporary password for {u['id']}: `{temp_pwd}`")
                                else:
                                    st.error(msg)

    # --------------------------------------------------------------------------
    # TAB 2: CREATE SINGLE ACCOUNT
    # --------------------------------------------------------------------------
    with tab_create:
        st.markdown("<h4>Provision New User Account</h4>", unsafe_allow_html=True)
        with st.form("create_single_user_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                n_id = st.text_input("User ID / Roll Number *", placeholder="e.g. S24CSEU0800")
                n_name = st.text_input("Full Name *", placeholder="e.g. Priya Sharma")
            with f_col2:
                n_email = st.text_input("Email Address *", placeholder="e.g. priya.sharma@campus.edu")
                n_role = st.selectbox("Role *", ["Student", "Admin"])

            n_password = st.text_input("Initial Password (leave blank to auto-generate)", type="password")

            create_submit = st.form_submit_button("Create Account", type="primary")

        if create_submit:
            ok, msg, temp_pwd = create_user(
                user_id=n_id,
                name=n_name,
                email=n_email,
                role=n_role,
                password=n_password if n_password.strip() else None,
                force_password_change=True if not n_password.strip() else False,
                actor_id=curr_user["id"]
            )
            if ok:
                st.success(f"User '{n_id}' created successfully!")
                if temp_pwd:
                    st.info(f"Auto-generated password: `{temp_pwd}` (User will be prompted to change on login).")
                st.rerun()
            else:
                st.error(msg)

    # --------------------------------------------------------------------------
    # TAB 3: BULK CSV IMPORT
    # --------------------------------------------------------------------------
    with tab_bulk:
        st.markdown("<h4>Bulk Import Accounts from CSV</h4>", unsafe_allow_html=True)
        st.markdown("""
        Upload a CSV file or paste formatted CSV lines. Required headers: `id,name,email`.
        Optional header: `role` (defaults to `Student`).
        """)

        st.code("id,name,email,role\nS24CSEU0710,Rahul Verma,rahul@campus.edu,Student\nADM005,Dr. K. Mehta,kmehta@campus.edu,Admin", language="csv")

        csv_file = st.file_uploader("Upload CSV File", type=["csv"], key="users_csv_uploader")
        csv_text_input = st.text_area("Or Paste CSV Text directly:", height=120, placeholder="id,name,email,role\n...")

        if st.button("Execute Bulk Import", type="primary", key="btn_run_bulk_import"):
            raw_text = ""
            if csv_file is not None:
                raw_text = csv_file.getvalue().decode("utf-8", errors="ignore")
            elif csv_text_input.strip():
                raw_text = csv_text_input.strip()

            if not raw_text:
                st.warning("Please upload a CSV file or paste CSV text first.")
            else:
                report = bulk_import_users_csv(raw_text, actor_id=curr_user["id"])
                st.markdown(f"**Import Summary:** {report['added']} added, {report['rejected']} rejected out of {report['total']} total rows.")

                if report["results"]:
                    for res in report["results"]:
                        if res["status"] == "PASS":
                            st.success(f"Row {res['row']}: Created {res['role']} `{res['id']}` ({res['name']}) · Temp Password: `{res['initial_password']}`")
                        else:
                            st.error(f"Row {res.get('row', 0)}: Failed — {res.get('reason', 'Unknown error')}")
