from selenium import webdriver
from selenium.webdriver.common.by import By

# Start a Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (without GUI)
driver = webdriver.Chrome(options=options)

# Open the YouTube video page
video_url = "https://www.youtube.com/watch?v=3lYP6AZ5gSI"
driver.get(video_url)

# Execute JavaScript to get video description
video_description = driver.execute_script(
    'return document.querySelector("#description").textContent;'
)

# Print the video description
print(video_description)

# Close the WebDriver
driver.quit()
