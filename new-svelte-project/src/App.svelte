<script lang="ts">
  import ApiTest from "./lib/apiTest.svelte";
</script>

<main class="min-h-screen px-4 py-8 bg-white">
  <div class="max-w-4xl mx-auto">
    <h1 class="mb-4 text-3xl font-bold text-center text-gray-800">
      Stable Diffusion API 테스트
    </h1>
    <div class="w-full">
      <ApiTest />
    </div>
  </div>
</main>
