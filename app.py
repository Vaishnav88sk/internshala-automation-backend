# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from internshala_bot.main import internshala  # Import the internshala class
# from internshala_bot.chat_gpt import chat
# from internshala_bot.generate_report import df_success, df_failed
# from playwright.sync_api import sync_playwright
# import asyncio
# import os

# app = Flask(__name__)
# CORS(app)

# # Initialize Playwright and the internshala instance
# with sync_playwright() as p:
#     args = ["--disable-blink-features=AutomationControlled"]
#     browser = p.chromium.launch(args=args, headless=False)  
#     intern = internshala(browser)
#     gpt = chat(intern.gpt_browser)
#     success = df_success()
#     failed = df_failed()



# @app.route('/api/internships', methods=['GET'])
# def get_internships():
#     # keywords = request.args.get('keywords', 'python')  # Default to 'python'
#     # filter_page_url = f"https://internshala.com/internships/{keywords}-internship/"
#     # internships = intern.fetch_internships(filter_page_url)
#     # print(f"Returning internships: {internships}")  # Debug log
#     # return jsonify(internships)
#     keywords = request.args.get("keywords", "").strip()  # Ensure no extra spaces
#     if not keywords:
#         return jsonify({"error": "No keywords provided"}), 400

#     print(f"Filtering Internships for: {keywords}")  # Debugging

#     # ✅ Ensure a proper URL is constructed
#     filter_page_url = f"https://internshala.com/internships/{keywords}-internship/"

#     try:
#         internships = intern.fetch_internships(filter_page_url)
#         print("Fetched Internships:", internships)  # Debugging

#         response_data = []
#         for i, internship_url in enumerate(internships):
#             response_data.append({
#                 "title": "N/A",  # No title info in just a URL
#                 "company": "N/A",
#                 "location": "N/A",
#                 "stipend": "N/A",
#                 "duration": "N/A",
#                 "link": internship_url,  # Directly use the URL
#             })


#         print("Final Response Data:", response_data)  # Debugging
#         return jsonify(response_data), 200

#     except Exception as e:
#         print(f"Error in get_internships: {e}")
#         return jsonify({"error": str(e)}), 500

# @app.route('/api/apply', methods=['POST'])
# def apply_to_internship():
#     # data = request.json
#     # internship_url = data.get('url')  # Use URL instead of ID for simplicity
#     # resume_path = os.path.join(os.path.dirname(__file__), 'internshala_bot/resume.txt')
    
#     # already_applied = intern.get_internship_info(internship_url)
#     # if not already_applied:
#     #     intern.update_resume_skills()
#     #     success_status = intern.apply_to_internship(gpt, success, failed, resume_path)
#     #     return jsonify({'status': 'success' if success_status else 'failed'})
#     # else:
#     #     return jsonify({'status': 'already_applied'})
#     try:
#         data = request.get_json()
#         print("Received data:", data)  # Log received data

#         internship_url = data.get("url")
#         if not internship_url or not internship_url.startswith("http"):
#             return jsonify({"status": "error", "message": "Invalid internship URL"}), 400

#         print("Applying to:", internship_url)  # Log valid URL

#         already_applied = intern.get_internship_info(internship_url)
#         if already_applied:
#             return jsonify({"status": "already_applied"}), 200

#         result = asyncio.run(intern.fill_app_form(internship_url))
#         if result:
#             return jsonify({"status": "success"}), 200
#         else:
#             return jsonify({"status": "error", "message": "Failed to apply"}), 500

#     except Exception as e:
#         print(f"Error in apply_to_internship: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify
from flask_cors import CORS
from internshala_bot.main import internshala  # Import the internshala class
from internshala_bot.chat_gpt import chat
from internshala_bot.generate_report import df_success, df_failed
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)
CORS(app)

# Initialize Playwright and Internshala bot
with sync_playwright() as p:
    args = ["--disable-blink-features=AutomationControlled"]
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
    )  
    intern = internshala(browser)
    gpt = chat(intern.gpt_browser)
    success = df_success()
    failed = df_failed()

@app.route('/api/internships', methods=['GET'])
def get_internships():
    keywords = request.args.get("keywords", "").strip()
    if not keywords:
        return jsonify({"error": "No keywords provided"}), 400

    print(f"Filtering Internships for: {keywords}")
    filter_page_url = f"https://internshala.com/internships/{keywords}-internship/"
    # internships = intern.fetch_internships(filter_page_url)
    # print("Fetched Internships:", internships)

    try:
        internships = intern.fetch_internships(filter_page_url)
        # print("Fetched Internships:", internships)

        # response_data = []
        # for url in internships:
        #     details = intern.get_internship_details(url)  # Fetch details from the page
        #     response_data.append({
        #         "title": details.get("title", "N/A"),
        #         "company": details.get("company", "N/A"),
        #         "location": details.get("location", "N/A"),
        #         "stipend": details.get("stipend", "N/A"),
        #         "duration": details.get("duration", "N/A"),
        #         "link": url
        #     })

        return internships, 200

    except Exception as e:
        print(f"Error in get_internships: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/apply', methods=['POST'])
def apply_to_internship():
    try:
        data = request.get_json()
        # print("Received data:", data)

        internship_url = data.get("url")
        if not internship_url or not internship_url.startswith("http"):
            return jsonify({"status": "error", "message": "Invalid internship URL"}), 400

        print("Applying to:", internship_url)

        already_applied = intern.get_internship_info(internship_url)
        if already_applied:
            return jsonify({"status": "already_applied"}), 200

        result = intern.fill_app_form(internship_url)  # No asyncio.run()

        return jsonify({"status": "success" if result else "error"}), 200 if result else 500

    except Exception as e:
        print(f"Error in apply_to_internship: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
