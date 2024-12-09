from rest_framework import serializers
from .models import MyUser ,Book,BorrowRequest
from django.utils.encoding import smart_str,force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class MyUserserializrs(serializers.ModelSerializer):
    password2=serializers.CharField(style={'input_type':'password'},write_only=True)
    class Meta:
        model=MyUser
        fields=["email","name","password","password2"]

        extra_kwargs={
            'password':{'write_only':True}
        }

    def validate(self, attrs):
        password=attrs.get("password")
        password2=attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError("Password and Confirm Password Doesn't Match")
        return attrs
    
    def create(self, validated_data):
        return MyUser.objects.create_user(**validated_data)
    
class MyUserLoginserializrs(serializers.ModelSerializer):
    email=serializers.EmailField(max_length=255)
    class Meta:
        model=MyUser
        fields=["email","password"]

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=MyUser
        fields=['id','email','name']

class ChangePasswordSerializers(serializers.Serializer):
    password=serializers.CharField(max_length=255, style={'input_type':'password'},write_only=True)
    password2=serializers.CharField(max_length=255,style={'input_type':'password'},write_only=True)
    class Meta:
        fields=["password","password2"]

    def validate(self, attrs):
        password=attrs.get('password')
        password2=attrs.get('password2')
        user=self.context.get('user')
        if password != password2:
            raise serializers.ValidationError("Password and Confirm Password Doesn't Match")
        user.set_password(password)
        user.save()
        return attrs
    
class allbookShow(serializers.ModelSerializer):
    class Meta:
        model=Book
        fields=['title','author','unique_code']

class BorrowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRequest
        fields = ['book', 'start_date', 'end_date']
    
    def validate(self, data):
        user = self.context['request'].user
        print(user)
        if user.is_librarian:
            print(user.is_library_user)
            raise serializers.ValidationError("Librarians cannot create borrow requests.")
        book = data['book']
        if not book.is_available:
            raise serializers.ValidationError("This book is not available for borrowing.")
        
        # Check for overlapping borrow requests
        if BorrowRequest.objects.filter(
            book=book, 
            status='approved', 
            start_date__lte=data['end_date'],
            end_date__gte=data['start_date']
        ).exists():
            raise serializers.ValidationError("The book is already borrowed during the requested dates.")
        
        return data
    

class BorrowRequestStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRequest
        fields = ['status']

    def validate_status(self, value):
        if value not in [BorrowRequest.APPROVED, BorrowRequest.DENIED]:
            raise serializers.ValidationError("Status must be 'Approved' or 'Denied'.")
        return value

class BorrowHistorySerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)

    class Meta:
        model = BorrowRequest
        fields = ['id', 'book_title', 'book_author', 'start_date', 'end_date', 'status']
    