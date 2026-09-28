from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.deps import CurrentUser, get_current_user, get_db
from app.schemas.quote_import import ImportSaveIn
from app.services import quote_import as svc

MAX_FILES = 20
MAX_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/api/v1/quotes/import", tags=["quote import"], dependencies=[Depends(get_current_user)])


@router.post("/read")
async def read(files: list[UploadFile] = File(...), db=Depends(get_db)):
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Upload up to {MAX_FILES} files at a time.")
    loaded = []
    for f in files:
        content = await f.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            loaded.append((f.filename or "file", b""))  # rejected below with a clear message
            continue
        loaded.append((f.filename or "file", content))
    results = svc.read_files(db, [(n, c) for n, c in loaded if c])
    too_big = [{"filename": n, "draft": None, "error": "The file is larger than 10 MB.", "already_imported": False,
                "customer_id": None} for n, c in loaded if not c]
    return results + too_big


@router.post("/save", status_code=201)
def save(body: ImportSaveIn, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    return svc.save(db, body, user)


@router.get("/owner")
def owner(db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    return svc.owner_info(db, user.id)
