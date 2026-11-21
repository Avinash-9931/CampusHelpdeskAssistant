"""
Knowledge Base page module for AI-Powered Campus Helpdesk Assistant.
Provides drag-and-drop PDF ingestion, real-time validation error reporting,
per-document cards with pages/chunks stats, delete confirmation dialogs,
reprocessing, summary metrics row, and 1-click Demo Policy loader.
"""

import streamlit as st
from datetime import datetime
from config import settings
from core.pdf_processor import (
    process_document,
    PDFProcessingError,
    InvalidFileTypeError,
    EmptyFileError,
    EmptyPDFError,
    FileTooLargeError,
    DuplicateFileError,
    PasswordProtectedPDFError,
    EncryptedPDFError,
    CorruptedPDFError,
    CorruptPDFError,
    ScannedPDFError
)
from core.text_chunker import chunk_pages
from ui.components import (
    render_icon,
    render_badge,
    render_empty_state,
    render_demo_banner
)


def load_demo_document():
    """Builds and indexes the synthetic demo university policy manual."""
    demo_pdf_path = settings.DEMO_DIR / "university_policy_demo.pdf"
    if not demo_pdf_path.exists():
        from data.demo.generate_demo_pdf import build_pdf
        build_pdf()

    with open(demo_pdf_path, "rb") as f:
        file_bytes = f.read()

    doc = process_document(file_bytes, filename="university_policy_demo.pdf")
    chunks = chunk_pages(doc.pages, filename=doc.filename)

    st.session_state.retriever.add_document(doc, chunks)
    st.session_state.demo_active = True


def render_knowledge_base_page():
    """Renders the Knowledge Base management view."""
    # Persistent Demo Warning Banner if active
    if st.session_state.get("demo_active", False):
        st.markdown(render_demo_banner(), unsafe_allow_html=True)

    st.markdown("<h2>Knowledge Base Management</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:var(--text-muted); margin-top:-6px; font-size:13.5px;'>"
        "Upload and manage official university PDF policies. Documents are validated, extracted per page, "
        "and indexed with page-level attribution."
        "</p>",
        unsafe_allow_html=True
    )

    retriever = st.session_state.retriever
    stats = retriever.get_stats()

    # 1. Summary Metrics Row
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Documents", stats["document_count"])
    with s2:
        st.metric("Extracted Pages", stats["total_pages"])
    with s3:
        st.metric("Indexed Chunks", stats["chunk_count"])
    with s4:
        st.metric("Active Retrieval", retriever.active_method())

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:20px 0;'>", unsafe_allow_html=True)

    # 2. Upload Section and Demo Loader
    up_col, demo_col = st.columns([1.8, 1.2], gap="large")

    with up_col:
        st.markdown(f"### Upload Official PDF Documents")
        st.markdown(
            f"<div style='font-size:12.5px; color:var(--text-muted); margin-bottom:12px;'>"
            f"Maximum file size: <strong>{settings.MAX_UPLOAD_MB} MB</strong> per PDF. Only official vector PDFs supported."
            f"</div>",
            unsafe_allow_html=True
        )

        uploaded_files = st.file_uploader(
            "Select university PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            help="Files undergo magic-byte (%PDF) verification, corruption checking, and scanned-image detection."
        )

        if uploaded_files:
            existing_hashes = retriever.get_existing_hashes()
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, uf in enumerate(uploaded_files):
                file_name = uf.name
                file_bytes = uf.read()
                status_text.markdown(f"Processing <code>{file_name}</code>...")

                try:
                    # Ingest using core.pdf_processor
                    doc = process_document(
                        file_bytes=file_bytes,
                        filename=file_name,
                        existing_hashes=existing_hashes
                    )
                    chunks = chunk_pages(doc.pages, filename=doc.filename)
                    retriever.add_document(doc, chunks)
                    existing_hashes.add(doc.hash)
                    st.success(f"✅ Successfully indexed **{file_name}** ({doc.page_count} pages, {len(chunks)} chunks).")
                except InvalidFileTypeError as e:
                    st.error(f"❌ **Invalid Format:** {str(e)}")
                except EmptyFileError as e:
                    st.error(f"❌ **Empty File:** {str(e)}")
                except EmptyPDFError as e:
                    st.error(f"❌ **Empty PDF Document:** {str(e)}")
                except FileTooLargeError as e:
                    st.error(f"❌ **Oversized Document:** {str(e)}")
                except DuplicateFileError as e:
                    st.warning(f"⚠️ **Duplicate Content:** {str(e)}")
                except (PasswordProtectedPDFError, EncryptedPDFError) as e:
                    st.error(f"🔒 **Encrypted PDF:** {str(e)}")
                except (CorruptedPDFError, CorruptPDFError) as e:
                    st.error(f"❌ **Corrupted PDF:** {str(e)}")
                except ScannedPDFError as e:
                    st.error(f"📄 **Scanned Document Detected:** {str(e)}")
                except Exception as e:
                    st.error(f"❌ **Processing Error:** {str(e)}")

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("Upload processing finished.")

    with demo_col:
        st.markdown("### Quick Demo Setup")
        st.markdown(f"""
        <div class="custom-card" style="margin-bottom:14px; padding:18px;">
            <div style="font-weight:700; color:var(--navy); font-size:14px; margin-bottom:6px;">
                Synthetic University Policy Handbook
            </div>
            <div style="font-size:12.5px; color:var(--text-muted); line-height:1.5;">
                Load the pre-built 4-page academic manual featuring attendance quotas (75%), 
                a deliberate late registration fee conflict ($50 vs $100), library guidelines, and departmental contacts.
            </div>
        </div>
        """, unsafe_allow_html=True)

        d_btn1, d_btn2 = st.columns([1, 1])
        with d_btn1:
            if st.button("📥 Load Demo Policy", type="primary", use_container_width=True, key="load_demo_btn"):
                with st.spinner("Generating and indexing demo policy document..."):
                    load_demo_document()
                st.success("✅ Demo document loaded into knowledge base!")
                st.rerun()

        with d_btn2:
            if stats["chunk_count"] > 0:
                if st.button("🗑️ Clear All", use_container_width=True, key="clear_all_kb_btn"):
                    st.session_state.confirm_clear_all = True

        if st.session_state.get("confirm_clear_all", False):
            st.warning("⚠️ Are you sure you want to delete all indexed documents?")
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("Yes, Clear Everything", type="primary", use_container_width=True):
                    retriever.clear_all()
                    st.session_state.demo_active = False
                    st.session_state.chat_history = []
                    st.session_state.confirm_clear_all = False
                    st.rerun()
            with c_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_all = False
                    st.rerun()

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:24px 0;'>", unsafe_allow_html=True)

    # 3. Currently Indexed Document Cards
    st.markdown("### Currently Indexed Documents")
    documents = retriever.list_documents()

    if not documents:
        st.markdown(
            render_empty_state(
                title="Knowledge Base is Empty",
                message="No official documents are indexed. Drag & drop a PDF above or click 'Load Demo Policy'.",
                icon_name="file-text"
            ),
            unsafe_allow_html=True
        )
    else:
        for doc in documents:
            fname = doc.get("filename", "document.pdf")
            page_count = doc.get("page_count", 0)
            chunk_count = doc.get("chunk_count", 0)
            uploaded_at = doc.get("uploaded_at", "Recently")
            size_kb = doc.get("size_bytes", 0) / 1024.0

            card_col, act_col = st.columns([4, 1.2])

            with card_col:
                st.markdown(f"""
                <div class="custom-card" style="padding:16px 20px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:700; color:var(--navy); font-size:14.5px; display:flex; align-items:center; gap:8px;">
                            {render_icon("file-text", size=16, color="#2563EB")} {fname}
                        </div>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
                            Uploaded: {uploaded_at} · Size: {size_kb:.1f} KB
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="badge badge-muted">{page_count} pages</span>
                        <span class="badge badge-accent">{chunk_count} chunks</span>
                        <span class="badge badge-success">{render_icon("check", size=11, color="#16A34A")} Indexed</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with act_col:
                btn_re, btn_del = st.columns(2)
                with btn_re:
                    if st.button("🔄 Reprocess", key=f"reproc_{fname}", use_container_width=True):
                        # Rebuild index for this document
                        retriever.rebuild_index()
                        st.success(f"Reprocessed index for {fname}.")
                        st.rerun()

                with btn_del:
                    if st.button("🗑️ Delete", key=f"del_{fname}", use_container_width=True):
                        st.session_state[f"confirm_del_{fname}"] = True

            # Confirmation prompt for deleting single document
            if st.session_state.get(f"confirm_del_{fname}", False):
                st.warning(f"Delete '{fname}' and remove all associated chunks?")
                del_c1, del_c2 = st.columns(2)
                with del_c1:
                    if st.button("Confirm Delete", key=f"conf_yes_{fname}", type="primary", use_container_width=True):
                        retriever.remove_document(fname)
                        if fname == "university_policy_demo.pdf":
                            st.session_state.demo_active = False
                        st.session_state[f"confirm_del_{fname}"] = False
                        st.rerun()
                with del_c2:
                    if st.button("Cancel", key=f"conf_no_{fname}", use_container_width=True):
                        st.session_state[f"confirm_del_{fname}"] = False
                        st.rerun()
