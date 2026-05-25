// Import the Firebase SDKs from a CDN
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-analytics.js";
const firebaseConfig = {
    apiKey: "AIzaSyCdYNOZDTnVdq3lgJ2k6-FfizS-vxYQkpY", //this key is safe to expose as it only allows authentication and has no admin privileges
    authDomain: "stockml-usertable.firebaseapp.com",
    databaseURL: "https://stockml-usertable-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "stockml-usertable",
    storageBucket: "stockml-usertable.firebasestorage.app",
    messagingSenderId: "216365895860",
    appId: "1:216365895860:web:89abe0e1b4d8350edb07e1",
    measurementId: "G-17CVM7SCHB"
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);

export { auth };

const makeSession = async (username) => {
    sessionStorage.setItem("username", username);
}


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