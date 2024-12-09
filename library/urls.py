from django.urls import path
from .views import RegisterApiView ,LoginApiView,ProfileApiView,PasschangeApi,BorrowRequestCreateAPIView,BorrowRequestApprovalAPIView,BorrowHistoryAPIView,DownloadBorrowHistoryCSV
urlpatterns = [
    # Api Path
    path('registre/',RegisterApiView.as_view(),name="registre"),
    path('login/',LoginApiView.as_view(),name="Login"),
    path('profile/',ProfileApiView.as_view(),name="profile"),
    path('passchange/',PasschangeApi.as_view(),name="passchange"),
    path('requestbook/',BorrowRequestCreateAPIView.as_view(),name="request"),
    path('approval/<int:pk>',BorrowRequestApprovalAPIView.as_view(),name="approvale"), 
    path('History/',BorrowHistoryAPIView.as_view(),name="history"), 
    path('download/', DownloadBorrowHistoryCSV.as_view(), name='download'), 

    # Project Path
    
]