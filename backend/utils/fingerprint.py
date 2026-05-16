FINGERPRINT_SCRIPT = """
<script>
(async function() {
    const fp = await (async () => {
        const { FingerprintJS } = await import('https://fpjscdn.net/v3');
        const agent = FingerprintJS.load();
        const result = await agent.get();
        return result.visitorId;
    })();
    // Gán vào biến toàn cục để các script khác dùng
    window.__fingerprint = fp;
})();
</script>
"""
