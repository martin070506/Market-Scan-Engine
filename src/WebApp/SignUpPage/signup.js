// Import the Firebase SDKs from a CDN
import { auth, API_BASE } from "../../env_Files/firebase.js";




document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("signup-button");
    if (button) {
        button.addEventListener("click", async (e) => {
            const username = document.getElementById("reg-email").value;
            const password = document.getElementById("reg-password").value;
            const confirmPassword = document.getElementById("reg-confirm").value;

            if (password !== confirmPassword) {
                alert("Passwords do not match!");
                return;
            }
            if (!isPasswordStrong(password)) {
                alert("Password must be at least 8 characters long and include uppercase, lowercase, number, and special character!");
                return;
            }
            if (!isUsernameEmail(username)) {
                alert("Username needs to be an email address!");
                return;
            }
            if (!isEqualToPassword(confirmPassword, password)) {
                alert("Passwords do not match!");
                return;
            }

            await makeDBSignUpRequest(username, password);
        });
    }
});


const makeDBSignUpRequest = async (username, password) => {
    createUserWithEmailAndPassword(auth, username, password)
        .then((userCredential) => {
            // Signed up successfully 
            const user = userCredential.user;
            console.log("User created successfully:", user.uid);
            makeSession(username);
            window.location.href = "../MainPage/index.html";
        })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            alert("Error during sign-up: " + errorMessage);
        });
}


const isUsernameEmail = (username) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(username);
}
const isPasswordStrong = (password) => {
    const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    return strongPasswordRegex.test(password);
}
const isEqualToPassword = (confirmPassword, password) => {
    return confirmPassword === password;
}