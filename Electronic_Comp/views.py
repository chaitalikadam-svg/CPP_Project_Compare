import boto3
from django.shortcuts import render, redirect,  get_object_or_404
from botocore.exceptions import ClientError
from django.http import HttpResponse
from boto3.dynamodb.conditions import Attr # helps to build a filter expression in dynamodb 
from .services.serpapi import normalize_products, fetch_google_shopping
import jwt
from .services.SNS import notify_admin_login
from boto3.dynamodb.conditions import Key
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from Electronic_Comp.s3_utils import get_presigned_image_url
import json 



#COGNITO_CLIENT_ID = '3ug6j8phjops063g71c7f7jj6'
#USER_POOL_ID = 'us-east-1_krK98JfRl'
#REGION = 'us-east-1'

#client = boto3.client('cognito-idp', region_name=REGION)
# Create your views here.

def signup_view(request):
    REGION = 'us-east-1'
    COGNITO_CLIENT_ID = '32fmfcd8rq4960i2d2gcl1l7t9'
    USER_POOL_ID = 'us-east-1_YVkvL1c61'
    client = boto3.client('cognito-idp', region_name=REGION)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if password != confirm_password:
            return render(request, 'signup.html', {
                'error': 'Oops, please check your password and confirm password'
            })
        try:
            client.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=email
            )
            # If no exception, user exists → redirect to signin
            return redirect('signin')

        except client.exceptions.UserNotFoundException:
            # Safe to proceed with signup
            pass

        try:
            client.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'preferred_username', 'Value': username}
                ]
            )
            request.session['signup_email'] = email
            return redirect('verify')

        except ClientError as e:
            return render(request, 'signup.html', {
                'error': f'Could not create account: {str(e)}'
            })

    return render(request, 'signup.html')


def verify_view(request):
    REGION = 'us-east-1'
    COGNITO_CLIENT_ID = '32fmfcd8rq4960i2d2gcl1l7t9'
    USER_POOL_ID = 'us-east-1_YVkvL1c61'
    
    client = boto3.client('cognito-idp', region_name=REGION)

    if request.method == 'POST':
        code = request.POST['code']
        email = request.session.get('signup_email')  # email saved during signup

        try:
            client.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,
                ConfirmationCode=code
            )
            return redirect('/signin/')   # go to signin page after successful verification
        except client.exceptions.CodeMismatchException:
            return render(request, 'verify.html', {'error': 'Invalid verification code'})
    return render(request, 'verify.html')
    
def signin_view(request):
    REGION = 'us-east-1'
    COGNITO_CLIENT_ID = '32fmfcd8rq4960i2d2gcl1l7t9'
    USER_POOL_ID = 'us-east-1_YVkvL1c61'
    
    client = boto3.client('cognito-idp', region_name=REGION)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        #print("DEBUG request.POST:", request.POST)
        #print("DEBUG email:", email)
        #print("DEBUG password:", password)

        try:
            response = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                },
                ClientId=COGNITO_CLIENT_ID
            )

            # Save tokens in session
            request.session['access_token'] = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            request.session['id_token'] = id_token

            # Decode the ID token to check Cognito groups
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            groups = decoded.get("cognito:groups", [])

            if "Admin" in groups:
                # Call SNS service
                notify_admin_login(email)

                # Render admin UI
                return render(request, 'add_product.html')
            else:
                # Render normal user UI
                return render(request, 'display.html')

        except client.exceptions.NotAuthorizedException:
            # Wrong password or invalid credentials
            return render(request, 'signin.html', {
                'error': 'Invalid email or password. Please try again.'
            })

        except client.exceptions.UserNotFoundException:
            # User doesn’t exist
            return render(request, 'signin.html', {
                'error': 'No account found with this email. Please sign up first.'
            })

        except ClientError as e:
            # Catch-all for other Cognito errors
            return render(request, 'signin.html', {
                'error': f'Login failed: {e.response["Error"]["Message"]}'
            })

    return render(request, 'signin.html')

def logout_view(request):
    request.session.flush()
    return redirect("signup")
    
def display_view(request):
    return render(request, "display.html")

def mobile_view(request):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")
    category = request.GET.get("category")

    # Scan DynamoDB
    if category:
        response = table.scan(FilterExpression=Attr("category").eq(category))
    else:
        response = table.scan()

    products = response.get("Items", [])

    # Attach competitor prices + pre-signed image URLs
    for product in products:
        query = product.get("name")
        if query:
            try:
                raw = fetch_google_shopping(query)
                product["competitor_prices"] = normalize_products(raw)
            except Exception as e:
                print(f"Error fetching competitor prices for {query}: {e}")
                product["competitor_prices"] = []
                product["error"] = str(e)

        product_id = product.get("productid")
        if product_id:
            product["image_url"] = get_presigned_image_url(product_id)

    return render(request, "mobile.html", {
        "category": category if category else "All",
        "products": products,
    })

def serpapi_search_view(request, product_name):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")
    response = table.scan(
        FilterExpression=Attr("name").eq(product_name)
    )
    items = response.get("Items", [])
    product = items[0] if items else None

    if not product:
        return render(request, "mobile.html", {
            "query": product_name,
            "products": [],
            "error": f"No product found in DynamoDB with name {product_name}",
        })
  # Using the product name directly for API
    query = f'"{product["name"]}"'
    raw = fetch_google_shopping(query)

    try:
        raw = fetch_google_shopping(query)
        competitor_prices = normalize_products(raw)

        # Render inside mobile.html so competitor prices appear inline
        return render(request, "mobile.html", {
            "query": query,
            "products": [product],   # your product details
            "competitor_prices": competitor_prices,
        })
    except Exception as e:
        return render(request, "mobile.html", {
            "query": query,
            "products": [product],
            "competitor_prices": [],
            "error": f"API error: {e}",
        })

def competitor_prices(request, productid):
    try:
        raw = fetch_google_shopping(productid)
        prices = normalize_products(raw)
        return render(request, "competitor_prices.html", {"prices": prices})
    except Exception as e:
        return render(request, "competitor_prices.html", {"error": str(e)})
        

def add_product_view(request):
    AWS_REGION = "us-east-1"
    BUCKET_NAME = "chaitalibucket1001"
    TABLE_NAME = "ElectronicItem"
    if request.method == "POST":
        category = request.POST.get("category")
        productid = request.POST.get("productid")
        name = request.POST.get("name")
        brand = request.POST.get("brand")
        model = request.POST.get("model")
        price = request.POST.get("price")
        warranty = request.POST.get("warranty")
        weightkg = request.POST.get("weightkg")
        specscore = request.POST.get("specscore")
        image_file = request.FILES.get("image")
        
        # parse features JSON if uploaded
        features = {}
        if "features_json" in request.FILES:
            try:
                features_file = request.FILES["features_json"]
                features = json.load(features_file)  # dict of key/value
            except Exception as e:
                messages.error(request, f"Invalid JSON file: {e}")
                return redirect("add_product")

        # S3 + DynamoDB clients
        s3 = boto3.client("s3", region_name=AWS_REGION)
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(TABLE_NAME)

        # Upload image first
        file_ext = image_file.name.split(".")[-1]
        s3_key = f"{productid}"

        try:
            s3.upload_fileobj(
                image_file.file,
                BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": image_file.content_type}
            )
        except Exception as e:
            messages.error(request, f"S3 Upload Error: {e}")
            return redirect("add_product")

        # Store record in DynamoDB
        item = {
            "category": category,
            "productid": productid,
            "name": name,
            "brand": brand,
            "model": model,
            "price": Decimal(price),
            "warranty": warranty,
            "weightkg": Decimal(weightkg),
            "specscoreoutof100": int(specscore),
            "features": features,
            "image_s3_key": s3_key
        }

        try:
            table.put_item(Item=item)
            messages.success(request, "Product saved successfully!")
        except Exception as e:
            messages.error(request, f"DynamoDB Error: {e}")

        return redirect("add_product")

    return render(request, "add_product.html")