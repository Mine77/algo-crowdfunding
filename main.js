const algo = require("./algo");
const algosdk = require('algosdk');

// Alice account: 2YI264DKCDYQX5XMVFAQYXBV3PRJATRBNUN2UKPYJGK6KWNRF6XYUVPHQA
const aliceMnemonic = "bench outdoor conduct easily pony normal memory boat tiger together catch toward submit web stomach insane other list clap grain photo excess crush absorb illness";
const aliceAccount = algosdk.mnemonicToSecretKey(aliceMnemonic);

// Bob account: B7K3C7ZOG5JMVMDZRUZ6HWWZYCXYBPNZADAP3MLTZE5MUA56DK4SU762M4
const bobMnemonic = "road pigeon recipe process tube voyage syrup favorite near harvest upset survey baby maze all hamster peace define human foil hurdle sponsor panda absorb lamp";
const bobAccount = algosdk.mnemonicToSecretKey(bobMnemonic);

// to deploy the app
// needs to compile approval.py and clear.py
algo.compileContract('approval.teal').then((approvalContract) => {
    algo.compileContract('clear.teal').then((clearContract) => {
        const approvalProgram = new Uint8Array(Buffer.from(approvalContract.result, 'base64'));
        const clearProgram = new Uint8Array(Buffer.from(clearContract.result, 'base64'));

        // for test purpose, we use 0 here as an example
        currentTime = 0;
        let appArgs = [];
        appArgs.push(new Uint8Array(algosdk.encodeUint64(currentTime)));
        appArgs.push(new Uint8Array(algosdk.encodeUint64(currentTime + 1*3600000)));
        appArgs.push(new Uint8Array(algosdk.encodeUint64(1000)));
        appArgs.push(new Uint8Array(Buffer.from(aliceAccount.addr)));
        appArgs.push(new Uint8Array(algosdk.encodeUint64(currentTime + 2*3600000)));
        algo.createApp(aliceAccount,approvalProgram,clearProgram,appArgs).then(console.log).catch(console.log);

        // // to compile the escrow contract
        // // needs to compile the escrow.py first: python3 escrow.py
        // // needs to enter the appId
        // const appId = 15987743;
        // algo.compileContract('escrow.teal').then((contract) => {
        //     const programBytes = Buffer.from(contract.result, 'base64');

        //     //then we need to do an update type of app call to store the escrow contract address in the app
        //     let appArgs = [];
        //     appArgs.push(new Uint8Array(Buffer.from(contract.hash)));
        //     algo.updateApp(aliceAccount,appId,approvalProgram,clearProgram,appArgs).then(console.log).catch(console.log);
        // }).catch(console.log);


    }).catch(console.log);
}).catch(console.log);








