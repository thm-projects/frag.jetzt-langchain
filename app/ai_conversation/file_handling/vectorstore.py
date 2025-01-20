import os
from typing import Iterable, Union
from uuid import UUID, uuid4
from langchain_chroma import Chroma
import magic
from app.ai_conversation.entities.uploaded_file_content import UploadedFileContent
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    BSHTMLLoader,
    UnstructuredXMLLoader,
    UnstructuredODTLoader,
    UnstructuredWordDocumentLoader,
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredRTFLoader,
)
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

TEXT_SEPARATORS = [
    "\n\n",
    "\n",
    " ",
    ".",
    ",",
    "\u200b",  # Zero-width space
    "\uff0c",  # Fullwidth comma
    "\u3001",  # Ideographic comma
    "\uff0e",  # Fullwidth full stop
    "\u3002",  # Ideographic full stop
    "",
]

TEXT_CHUNK_SIZE = 200
TEXT_CHUNK_OVERLAP = 0

CODE_CHUNK_SIZE = 250
CODE_CHUNK_OVERLAP = 0

CSS_SEPARATORS = [
    # CSS selectors, also SCSS mixins and functions
    "[^\n][ \t]*[^{\n]+{[ \t\n$]+",
    # CSS properties
    "\n[ \t]*\\S+[ \t]*:",
    # standard delimiters
    *TEXT_SEPARATORS,
]

JSON_SEPARATORS = [
    *TEXT_SEPARATORS[:2],
    # JSON keys
    '\n\\s*"[^"]+":',
    # standard delimiters
    *TEXT_SEPARATORS[2:],
]

# TODO: Add semantic splitter
standard_text_splitter = RecursiveCharacterTextSplitter(
    separators=TEXT_SEPARATORS,
    chunk_size=TEXT_CHUNK_SIZE,
    chunk_overlap=TEXT_CHUNK_OVERLAP,
)

chroma: Chroma = None


def set_chroma(chroma_instance: Chroma):
    global chroma
    chroma = chroma_instance


def get_chroma():
    global chroma
    return chroma


def _get_splitter_for_language(
    language: Language, code: bool = True
) -> RecursiveCharacterTextSplitter:
    seperators = RecursiveCharacterTextSplitter.get_separators_for_language(language)
    if language not in [Language.LATEX, Language.HTML, Language.COBOL]:
        seperators = [*seperators[:-4], *TEXT_SEPARATORS]
    return RecursiveCharacterTextSplitter(
        separators=seperators,
        is_separator_regex=True,
        chunk_size=CODE_CHUNK_SIZE if code else TEXT_CHUNK_SIZE,
        chunk_overlap=CODE_CHUNK_OVERLAP if code else TEXT_CHUNK_OVERLAP,
    )


def _add_ref(content: UploadedFileContent, docs: Iterable[Document]) -> None:
    for doc in docs:
        del doc.metadata["source"]
        doc.metadata["ref_id"] = str(content.id)


# https://python.langchain.com/docs/integrations/document_loaders/
async def import_to_vectorstore(
    content: UploadedFileContent, custom_path: str = None
) -> Union[str, bool]:
    path = (
        custom_path
        if custom_path is not None
        else f"{os.getcwd()}/files/{content.file_ref}"
    )
    mime_type = magic.from_file(path, mime=True)
    docs = []
    before_docs = []
    match mime_type:
        case (
            "audio/aac",
            "audio/midi",
            "application/x-cdf",
            "audio/midi",
            "audio/x-midi",
            "audio/mpeg",
            "audio/ogg",
            "audio/wav",
            "audio/webm",
            "audio/3gpp",
            "audio/3gpp2",
        ):  # audio
            # TODO: AssemblyAI
            # https://python.langchain.com/docs/integrations/document_loaders/assemblyai/
            return "Not supported"
        case (
            "image/jpeg",
            "image/png",
            "image/bmp",
            "image/svg+xml",
            "image/tiff",
        ):  # images
            # https://python.langchain.com/docs/integrations/document_loaders/image_captions/
            # https://python.langchain.com/docs/integrations/document_loaders/image/ or document parsing?
            return "Not supported"
        case (
            "image/gif",
            "image/apng",
            "image/avif",
            "image/webp",
            "image/vnd.microsoft.icon",
        ):  # images with more frames
            # TODO: Currently not implemented (with video)
            return "Not supported"
        case (
            "video/x-msvideo",
            "video/mp4",
            "video/mpeg",
            "video/ogg",
            "application/ogg",
            "video/mp2t",
            "video/webm",
            "video/3gpp",
            "video/3gpp2",
        ):  # video
            # TODO: Currently not implemented
            return "Not supported"
        case (
            "application/x-abiword",
            "application/vnd.oasis.opendocument.presentation",
            "application/vnd.oasis.opendocument.spreadsheet",
        ):  # documents
            return "Not supported"
        case (
            "application/vnd.amazon.ebook",
            "application/epub+zip",
        ):  # books, publications
            return "Not supported"
        case (
            "application/x-freearc",
            "application/x-bzip",
            "application/x-bzip2",
            "application/gzip",
            "application/x-gzip",
            "application/vnd.rar",
            "application/x-tar",
            "application/zip",
            "application/x-zip-compressed",
            "application/x-7z-compressed",
        ):  # archives
            return "Not supported"
        case (
            "application/vnd.ms-fontobject",
            "font/otf",
            "font/ttf",
            "font/woff",
            "font/woff2",
        ):  # fonts
            return "Not supported"
        case (
            "application/octet-stream",
            "text/calendar",
            "application/java-archive",
            "application/vnd.apple.installer+xml",
            "application/vnd.visio",
            "application/vnd.mozilla.xul+xml",
        ):  # not allowed
            return "Not Allowed"
        case "application/vnd.oasis.opendocument.text":
            # https://python.langchain.com/docs/integrations/document_loaders/odt/
            before_docs = await UnstructuredODTLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "text/plain":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "text/css":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = RecursiveCharacterTextSplitter(
                separators=CSS_SEPARATORS,
                is_separator_regex=True,
                chunk_size=CODE_CHUNK_SIZE,
                chunk_overlap=CODE_CHUNK_OVERLAP,
            )
            docs = splitter.split_documents(before_docs)
        case "text/javascript":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = _get_splitter_for_language(Language.JS)
            docs = splitter.split_documents(before_docs)
        case "application/json":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = RecursiveCharacterTextSplitter(
                separators=JSON_SEPARATORS,
                is_separator_regex=True,
                chunk_size=TEXT_CHUNK_SIZE,
                chunk_overlap=TEXT_CHUNK_OVERLAP,
            )
            docs = splitter.split_documents(before_docs)
        case "application/ld+json":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = RecursiveCharacterTextSplitter(
                separators=JSON_SEPARATORS,
                is_separator_regex=True,
                chunk_size=TEXT_CHUNK_SIZE,
                chunk_overlap=TEXT_CHUNK_OVERLAP,
            )
            docs = splitter.split_documents(before_docs)
        case "text/csv":
            # TODO: Better splitter with header? or UnstructuredCSVLoader
            # https://python.langchain.com/docs/integrations/document_loaders/csv/
            before_docs = await CSVLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/x-latex", "application/x-tex":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = _get_splitter_for_language(Language.LATEX)
            docs = splitter.split_documents(before_docs)
        case "text/html":
            # https://python.langchain.com/docs/integrations/document_loaders/bshtml/
            before_docs = await BSHTMLLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/xhtml+xml", "application/xml", "text/xml":
            # https://python.langchain.com/docs/integrations/document_loaders/xml/
            before_docs = await UnstructuredXMLLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            # unstructured or normal?
            # https://python.langchain.com/docs/integrations/document_loaders/microsoft_word/#using-unstructured
            before_docs = await UnstructuredWordDocumentLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/pdf":
            # TODO: Improve with images etc
            # https://python.langchain.com/docs/integrations/document_loaders/#pdfs
            before_docs = await PyPDFLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/x-httpd-php":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            splitter = _get_splitter_for_language(Language.PHP)
            docs = splitter.split_documents(before_docs)
        case (
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ):
            # https://python.langchain.com/docs/integrations/document_loaders/microsoft_powerpoint/
            before_docs = await UnstructuredPowerPointLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case (
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ):
            # https://python.langchain.com/docs/integrations/document_loaders/microsoft_excel/
            before_docs = await UnstructuredExcelLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/rtf":
            before_docs = await UnstructuredRTFLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case "application/x-sh", "application/x-csh":
            before_docs = await TextLoader(path).aload()
            _add_ref(content, before_docs)
            docs = standard_text_splitter.split_documents(before_docs)
        case _:
            return "Unknown MIME type: " + mime_type
    if docs:
        global chroma
        for doc in docs:
            doc.metadata["id"] = str(uuid4())
        if custom_path is not None:
            print(f"Inserting {len(docs)} documents for {content.id} with custom path")
        await chroma.aadd_documents(docs, ids=[doc.metadata["id"] for doc in docs])
        if custom_path is not None:
            return before_docs
    return True


async def on_content_deleted(ref_ids: list[UUID]):
    if len(ref_ids) < 1:
        return
    PAGE_SIZE = 1000
    has_remaining_elements = True
    global chroma
    while has_remaining_elements:
        result = chroma.get(
            where={"ref_id": {"$in": list(map(lambda x: str(x), ref_ids))}},
            include=[],
            limit=PAGE_SIZE,
        )
        ids = result["ids"]
        has_remaining_elements = len(ids) >= PAGE_SIZE
        if len(ids) > 0:
            await chroma.adelete(ids)
