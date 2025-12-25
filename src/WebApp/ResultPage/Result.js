const resultId = JSON.parse(localStorage.getItem("resultId") || {});
console.log("Loaded ID:", resultId)
const API_BASE = "https://market-scan-engine.onrender.com";


async function fetchResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const resultId = urlParams.get('id');
    const CupHandleResp = await fetch(`${API_BASE}/results/${resultId}/cup-handle`);
    const CupHandleData = await CupHandleResp.json().catch(() => ({}));
    console.log("Cup & Handle Stocks:", CupHandleData.stocks);
    //DATA here is our returned list of stocks, so we will need to choose how to display each index
    //for example index 0 is a list of all C&H stocks, index 1 is all Double Bottom Stocks and so on

    const DoubleBottomResp = await fetch(`${API_BASE}/results/${resultId}/double-bottom`);
    const DoubleBottomData = await DoubleBottomResp.json().catch(() => ({}));
    console.log("Double Bottom Stocks:", DoubleBottomData.stocks);
    //DATA here is our returned list of stocks, so we will need to choose how to display each index
    //for example index 0 is a list of all C&H stocks, index 1 is all Double Bottom Stocks and so on

    const CloseTo150Resp = await fetch(`${API_BASE}/results/${resultId}/close-to-150`);
    const CloseTo150Data = await CloseTo150Resp.json().catch(() => ({}));
    console.log("Close to 150$ Stocks:", CloseTo150Data.stocks);
    //DATA here is our returned list of stocks, so we will need to choose how to display each index
    //for example index 0 is a list of all C&H stocks, index 1 is all Double Bottom Stocks and so on
}
fetchResults();
