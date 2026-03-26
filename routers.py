from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from database import database, get_db
from models import Speaker, SpeakerOut, User, UserOut
from sqlalchemy.orm import Session
import tempfile
import os
import numpy as np
import librosa
import bcrypt

try:
	from resemblyzer import VoiceEncoder, preprocess_wav
except Exception:
	VoiceEncoder = None
	preprocess_wav = None

router = APIRouter()


encoder = None


def get_encoder():
	global encoder
	if encoder is None and VoiceEncoder is not None:
		try:
			encoder = VoiceEncoder()
		except Exception as e:
			print(f"Error loading encoder: {e}")
	return encoder


@router.post("/auth/register", response_model=UserOut)
async def register_user(
	username: str = Form(...),
	password: str = Form(...),
	db: Session = Depends(get_db),
):
	existing = db.query(User).filter(User.username == username).first()
	if existing:
		raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

	password_bytes = password.encode("utf-8")
	hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

	is_admin = username.lower() == "admin"

	user = User(
		username=username,
		password_hash=hashed,
		is_admin=is_admin,
		created_at=datetime.utcnow(),
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


@router.post("/auth/login")
async def login_user(
	username: str = Form(...),
	password: str = Form(...),
	db: Session = Depends(get_db),
):
	user = db.query(User).filter(User.username == username).first()
	if not user:
		raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")

	password_bytes = password.encode("utf-8")
	if not bcrypt.checkpw(password_bytes, user.password_hash.encode("utf-8")):
		raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")

	return {
		"username": user.username,
		"is_admin": user.is_admin,
		"id": user.id,
	}

#register speaker
@router.post("/speakers/enroll")
async def enroll(name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
	encoder = get_encoder()
	if encoder is None or preprocess_wav is None:
		raise HTTPException(status_code=500, detail="Voice encoder not available. Install resemblyzer and dependencies")

	tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
	try:
		content = await file.read()
		tmp.write(content)
		tmp.flush()
		tmp.close()

		try:
			wav_np, sr = librosa.load(tmp.name, sr=16000)
			if np.max(np.abs(wav_np)) < 0.001:
				raise HTTPException(status_code=400, detail="Аудиофайл слишком тихий или пустой")
		except Exception as e:
			raise HTTPException(status_code=400, detail=f"Ошибка загрузки аудио: {str(e)}")

		try:
			wav = preprocess_wav(tmp.name)
		except Exception:
			wav = wav_np

		embedding = encoder.embed_utterance(wav)
		embedding_list = embedding.tolist()

		if np.max(np.abs(embedding)) < 0.001:
			raise HTTPException(
				status_code=400,
				detail="Не удалось создать эмбеддинг из аудио. Проверьте качество файла",
			)

		speaker = Speaker(name=name, embedding=embedding_list, created_at=datetime.utcnow())
		db.add(speaker)
		db.commit()
		db.refresh(speaker)

		return {"id": speaker.id, "name": speaker.name}
	finally:
		try:
			os.unlink(tmp.name)
		except Exception:
			pass

#identify speaker
@router.post("/speakers/identify")
async def identify(file: UploadFile = File(...), db: Session = Depends(get_db)):
	encoder = get_encoder()
	if encoder is None or preprocess_wav is None:
		raise HTTPException(status_code=500, detail="Voice encoder not available. Install resemblyzer and dependencies")

	tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
	try:
		content = await file.read()
		tmp.write(content)
		tmp.flush()
		tmp.close()

		try:
			wav_np, sr = librosa.load(tmp.name, sr=16000)
			if np.max(np.abs(wav_np)) < 0.001:
				raise HTTPException(status_code=400, detail="Аудиофайл слишком тихий или пустой")
		except Exception as e:
			raise HTTPException(status_code=400, detail=f"Ошибка загрузки аудио: {str(e)}")

		try:
			wav = preprocess_wav(tmp.name)
		except Exception:
			wav = wav_np

		emb = encoder.embed_utterance(wav)

		speakers = db.query(Speaker).all()
		if not speakers:
			return {"match": None, "score": 0.0}

		best = None
		best_score = -1.0
		for sp in speakers:
			vec = np.array(sp.embedding)
			score = float(np.dot(emb, vec) / (np.linalg.norm(emb) * np.linalg.norm(vec) + 1e-10))
			if score > best_score:
				best_score = score
				best = sp

		threshold = 0.65
		if best_score >= threshold and best is not None:
			return {"match": best.name, "score": best_score}
		else:
			return {"match": None, "score": best_score}
	finally:
		try:
			os.unlink(tmp.name)
		except Exception:
			pass


@router.get("/speakers", response_model=list[SpeakerOut])
async def list_speakers(db: Session = Depends(get_db)):
	speakers = db.query(Speaker).order_by(Speaker.created_at.desc()).all()
	return speakers

