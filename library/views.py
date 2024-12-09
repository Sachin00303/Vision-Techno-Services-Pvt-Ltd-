from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import MyUserserializrs,MyUserLoginserializrs,ProfileSerializer,ChangePasswordSerializers,allbookShow,BorrowRequestSerializer ,BorrowRequestStatusUpdateSerializer,BorrowHistorySerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import Book,MyUser,BorrowRequest
import csv
from django.http import HttpResponse

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterApiView(APIView):
    def post(self,request,format=None):
        serializer=MyUserserializrs(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user=serializer.save()
            return Response({"msg":"registetion successfull"},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginApiView(APIView):
    def post(self,request,format=None):
        serializer=MyUserLoginserializrs(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email=serializer.data.get("email")
            password=serializer.data.get("password")
            user=authenticate(email=email,password=password)
            if user is not None:
                if user.is_librarian:
                    books = Book.objects.all()
                else:
                    books = Book.objects.filter(is_available=True) 
                serialized_books = allbookShow(books, many=True)
                token=get_tokens_for_user(user)
                return Response({"Token":token,"book_list": serialized_books.data},status=status.HTTP_201_CREATED)
            else:
                return Response({'errors':{'None field Errors',['Email and password Not found']}},status=status.HTTP_404_NOT_FOUND)
            
class ProfileApiView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request,format=None):
        serializer=ProfileSerializer(request.user)
        return Response(serializer.data , status=status.HTTP_200_OK)

class PasschangeApi(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request,format=None):
        serializer=ChangePasswordSerializers(data=request.data,context={'user':request.user})
        if serializer.is_valid(raise_exception=True):
            return Response({"msg":"Password change successfull"},status=status.HTTP_200_OK)
        return Response({'errors':{'None field Errors',['password Not found']}},status=status.HTTP_404_NOT_FOUND)

class BorrowRequestCreateAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.is_librarian:
            return Response({"error": "Librarians cannot create borrow requests."}, status=status.HTTP_403_FORBIDDEN)

        serializer = BorrowRequestSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            borrow_request = serializer.save(user=user)
            return Response({
                "message": "Borrow request created successfully.",
                "request_id": borrow_request.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class BorrowRequestApprovalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_librarian:
            return Response({"error": "You are not authorized to approve or deny borrow requests."},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            borrow_request = BorrowRequest.objects.get(id=pk)
        except BorrowRequest.DoesNotExist:
            return Response({"error": "Borrow request not found."}, status=status.HTTP_404_NOT_FOUND)
        if borrow_request.status != BorrowRequest.PENDING:
            return Response({"error": "Only pending requests can be updated."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = BorrowRequestStatusUpdateSerializer(borrow_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Borrow request updated successfully.", "data": serializer.data},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
from rest_framework.pagination import PageNumberPagination

class BorrowHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 10

        if request.user.is_librarian:
            borrow_requests = BorrowRequest.objects.all()
        else:
            borrow_requests = BorrowRequest.objects.filter(user=request.user)

        result_page = paginator.paginate_queryset(borrow_requests, request)
        serializer = BorrowHistorySerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
class DownloadBorrowHistoryCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        if request.user.is_librarian:
            borrow_requests = BorrowRequest.objects.all()
        else:
            borrow_requests = BorrowRequest.objects.filter(user=request.user)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="borrow_history.csv"'
        writer = csv.writer(response)
        writer.writerow(['Book Title', 'Book Author', 'Start Date', 'End Date', 'Status'])

        for request in borrow_requests:
            writer.writerow([
                request.book.title,
                request.book.author,
                request.start_date,
                request.end_date,
                request.status,
            ])

        return response