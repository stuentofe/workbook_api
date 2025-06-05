from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 각 워크북 API 라우터 불러오기
from api.inserting import router as inserting_router
from api.ordering import router as ordering_router
from api.verbrewrite import router as verbrewrite_router
# 앞으로 추가될 유형들도 여기에 계속 include 하면 됨

app = FastAPI()

# CORS 설정 - 티스토리에서 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://easyenough.tistory.com"],  # 개발 중엔 ["*"]로 테스트 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 각각의 기능 라우터 등록
app.include_router(inserting_router)
app.include_router(ordering_router)
app.include_router(verbrewrite_router)
