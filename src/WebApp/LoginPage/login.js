import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-analytics.js";
const firebaseConfig = {
    apiKey: "AIzaSyCdYNOZDTnVdq3lgJ2k6-FfizS-vxYQkpY",
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
    const button = document.getElementById("log-btn");
    if (button) {
        button.addEventListener("click", async (e) => {
            const username = document.getElementById("log-email").value;
            const password = document.getElementById("log-pass").value;




            // If all validations pass, proceed with sign-up
            await makeDBLoginUpRequest(username, password);
        });
    }
});


const makeDBLoginUpRequest = async (username, password) => {
    signInWithEmailAndPassword(auth, username, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User logged in successfully:", user.uid);
            makeSession(username);
            window.location.href = "../MainPage/index.html";
        })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            alert("Error during login: " + errorMessage);
        });
}



