from flask import Flask, request, jsonify
from flask_cors import CORS
from internshala_bot.main import internshala  # Import the Internshala class
from internshala_bot.chat_gpt import chat
from internshala_bot.generate_report import df_success, df_failed
from playwright.sync_api import sync_playwright
import configparser
import atexit

app = Flask(__name__)
CORS(app)

# Global Variables
intern = None
gpt = None
success = None
failed = None
p = None
browser = None


# Initialize Playwright + Bot
# def start_bot():
#     global intern, gpt, success, failed, p, browser

#     print("Starting Playwright and Internshala Bot...")

#     p = sync_playwright().start()

#     browser = p.chromium.launch(
#         headless=False,
#         args=[
#             "--disable-blink-features=AutomationControlled",
#             "--start-maximized"
#         ]
#     )

#     intern = internshala(browser)
#     gpt = chat(intern.gpt_browser)
#     success = df_success()
#     failed = df_failed()


# Cleanup resources on exit
@atexit.register
def cleanup():
    print("Cleaning up Playwright resources...")
    if browser:
        browser.close()
    if p:
        p.stop()


# Start the bot when Flask starts
# start_bot()


@app.route('/api/internships', methods=['GET'])
def get_internships():
    # if intern is None:
    #     print("INTERN OBJECT IS NONE!")
    #     return jsonify({"error": "Bot Not Initialized"}), 500

    keywords = request.args.get("keywords", "").strip()
    stipend = request.args.get("stipend", "").strip()
    if not keywords:
        return jsonify({"error": "No keywords provided"}), 400

    print(f"Filtering Internships for: {keywords}")
    if stipend:
        filter_page_url = f"https://internshala.com/internships/{keywords}-internship/stipend-{stipend}"
    else:
        filter_page_url = f"https://internshala.com/internships/{keywords}-internship/"

    try:
        with sync_playwright() as p:
            # browser = p.chromium.launch(headless=True)
            # intern = internshala(browser)
            internships = internshala.fetch_internships(filter_page_url)
            # browser.close()
            return internships, 200

    except Exception as e:
        print(f"Error in get_internships: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/apply', methods=['POST'])
def app_to_internship():
    # if intern is None:
    #     print("INTERN OBJECT IS NONE!")
    #     return jsonify({"error": "Bot Not Initialized"}), 500

    try:
        data = request.get_json()
        print("Received data:", data)

        internship_url = data.get("url")
        print("Internship URL:", internship_url)

        resume_path = "/Vaishnav_Kale_ResumeC3.pdf"
    
        success = []
        failed = []

        if not internship_url or not internship_url.startswith("http"):
            print("Invalid URL")
            return jsonify({"status": "error", "message": "Invalid internship URL"}), 400

        print("Applying to:", internship_url)

        # already_applied = intern.get_internship_info(internship_url)
        # print("Already Applied Status:", already_applied)

        # if already_applied:
        #     return jsonify({"status": "already_applied"}), 200

        # result = intern.apply_to_internship(internship_url, gpt, success, failed, resume_path)
        print("Form Filled Result:", result)

        return jsonify({"status": "success" if result else "error"}), 200 if result else 500

    except Exception as e:
        print(f"Error in apply_to_internship: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)
