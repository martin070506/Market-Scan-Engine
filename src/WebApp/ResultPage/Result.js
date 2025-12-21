const data = JSON.parse(localStorage.getItem("scanResult") || {});
localStorage.removeItem("scanResult");
console.log("Loaded Result:", data)
//DATA here is our returned list of stocks, so we will need to choose how to display each index
//for example index 0 is a list of all C&H stocks, index 1 is all Double Bottom Stocks and so on