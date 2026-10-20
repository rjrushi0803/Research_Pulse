# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine, select
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import StaticPool

# from app.main import create_app
# from app.models.user import User
# from app.psql_db import Base, get_db


# @pytest.fixture
# def test_environment():
#     # Share one in-memory database connection across the test.
#     test_engine = create_engine(
#         "sqlite://",
#         connect_args={"check_same_thread": False},
#         poolclass=StaticPool,
#     )
#     TestSession = sessionmaker(
#         bind=test_engine,
#         autoflush=False,
#         expire_on_commit=False,
#     )
#     Base.metadata.create_all(bind=test_engine)

#     app = create_app(initialize_db=False)

#     def override_get_db():
#         db = TestSession()
#         try:
#             yield db
#         finally:
#             db.close()

#     app.dependency_overrides[get_db] = override_get_db

#     with TestClient(app) as client:
#         yield client, TestSession

#     app.dependency_overrides.clear()
#     Base.metadata.drop_all(bind=test_engine)
#     test_engine.dispose()


# def test_onboarding_page_loads(test_environment):
#     client, _ = test_environment

#     response = client.get("/")

#     assert response.status_code == 200
#     assert "Research Pulse" in response.text
#     assert 'name="email"' in response.text
#     assert 'name="keywords"' in response.text


# def test_create_profile_saves_user(test_environment):
#     client, TestSession = test_environment

#     response = client.post(
#         "/setup",
#         data={
#             "email": "Researcher@Example.com",
#             "keywords": "AI in drug discovery, RAG\nBiomedical NLP",
#             "description": "Find recent AI research papers.",
#         },
#     )

#     assert response.status_code == 201
#     assert "Profile created" in response.text

#     with TestSession() as db:
#         user = db.scalar(select(User).where(User.email == "researcher@example.com"))

#         assert user is not None
#         assert user.research_keywords == [
#             "AI in drug discovery",
#             "RAG",
#             "Biomedical NLP",
#         ]
#         assert user.research_description == ("Find recent AI research papers.")


# def test_duplicate_email_is_rejected(test_environment):
#     client, _ = test_environment

#     data = {
#         "email": "researcher@example.com",
#         "keywords": "RAG",
#         "description": "Research interests",
#     }

#     first_response = client.post("/setup", data=data)
#     second_response = client.post(
#         "/setup",
#         data={**data, "email": "RESEARCHER@example.com"},
#     )

#     assert first_response.status_code == 201
#     assert second_response.status_code == 409
#     assert "already exists" in second_response.text


# # def test_invalid_email_is_rejected(test_environment):
# #     client, TestSession = test_environment

# #     response = client.post(
# #         "/setup",
# #         data={
# #             "email": "not-an-email",
# #             "keywords": "RAG",
# #             "description": "",
# #         },
# #     )

# #     assert response.status_code == 422
# #     assert "valid email address" in response.text

# #     with TestSession() as db:
# #         assert db.scalar(select(User)) is None


# def test_keywords_are_deduplicated(test_environment):
#     client, TestSession = test_environment

#     response = client.post(
#         "/setup",
#         data={
#             "email": "reader@example.com",
#             "keywords": "RAG, rag,  AI in drug discovery, RAG",
#             "description": "",
#         },
#     )

#     assert response.status_code == 201

#     with TestSession() as db:
#         user = db.scalar(select(User).where(User.email == "reader@example.com"))
#         assert user.research_keywords == [
#             "RAG",
#             "AI in drug discovery",
#         ]
