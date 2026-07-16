import { auth, API_BASE } from "../../env_Files/firebase.js";
import { signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";



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
            window.location.href = "../MainPage/index.html";
        })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            alert("Error during login: " + errorMessage);
        });
}



