// static/js/wallet.js

async function connectWallet() {
  const button = document.getElementById('connect-wallet-btn');
  const display = document.getElementById('wallet-address');
  const hiddenInput = document.getElementById('walletAddress');

  if (!window.ethereum) {
    alert('找不到錢包，請先在瀏覽器安裝 MetaMask 或其他以太坊錢包外掛。');
    return;
  }

  try {
    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts',
    });

    const address = accounts[0];

    const short = address.slice(0, 6) + '...' + address.slice(-4);
    if (button) {
      button.textContent = '已連接：' + short;
      button.disabled = true;
    }

    if (display) {
      display.textContent = address;
    }

    if (hiddenInput) {
      hiddenInput.value = address;
    }
  } catch (err) {
    console.error(err);
    alert('連接錢包失敗，可能是使用者取消或錢包發生錯誤。');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('connect-wallet-btn');
  if (button) {
    button.addEventListener('click', connectWallet);
  }
});
