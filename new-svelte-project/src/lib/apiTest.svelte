<script lang="ts">
  import { onMount } from "svelte";

  let prompt = "";
  let negativePrompt = "";
  let steps = 20;
  let width = 512;
  let height = 512;
  let isLoading = false;
  let generatedImage: string | null = null;
  let errorMessage: string | null = null;

  async function generateImage() {
    isLoading = true;
    generatedImage = null;
    errorMessage = null;

    try {
      const payload = {
        prompt: prompt,
        negative_prompt: negativePrompt,
        steps: steps,
        width: width,
        height: height,
        cfg_scale: 7,
        sampler_name: "Euler a",
      };

      const response = await fetch("http://127.0.0.1:7861/sdapi/v1/txt2img", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(
          `API 요청 실패: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if (data.images && data.images.length > 0) {
        // base64 이미지를 표시
        generatedImage = `data:image/png;base64,${data.images[0]}`;
      } else {
        throw new Error("이미지가 생성되지 않았습니다.");
      }
    } catch (error) {
      console.error("이미지 생성 중 오류:", error);
      errorMessage =
        error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="w-full">
  <div class="p-8 mb-8 shadow-sm bg-gray-50 rounded-2xl">
    <div class="mb-4">
      <label for="prompt" class="block mb-1 text-sm font-medium text-gray-700"
        >프롬프트</label
      >
      <textarea
        id="prompt"
        bind:value={prompt}
        rows="3"
        class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="프롬프트 입력"
      ></textarea>
    </div>

    <div class="mb-4">
      <label
        for="negative-prompt"
        class="block mb-1 text-sm font-medium text-gray-700"
        >네거티브 프롬프트</label
      >
      <textarea
        id="negative-prompt"
        bind:value={negativePrompt}
        rows="2"
        class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="원치 않는 요소 지정"
      ></textarea>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4">
      <div>
        <label for="steps" class="block mb-1 text-sm font-medium text-gray-700"
          >스텝:</label
        >
        <input
          id="steps"
          type="number"
          bind:value={steps}
          min="1"
          max="150"
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label for="width" class="block mb-1 text-sm font-medium text-gray-700"
          >너비:</label
        >
        <input
          id="width"
          type="number"
          bind:value={width}
          min="64"
          max="2048"
          step="64"
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label for="height" class="block mb-1 text-sm font-medium text-gray-700"
          >높이:</label
        >
        <input
          id="height"
          type="number"
          bind:value={height}
          min="64"
          max="2048"
          step="64"
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>

    <button
      on:click={generateImage}
      disabled={isLoading}
      class="w-full px-4 py-2 font-medium text-white transition duration-200 bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? "이미지 생성 중..." : "이미지 생성하기"}
    </button>
  </div>

  <div class="flex flex-col items-center justify-center min-h-48">
    {#if isLoading}
      <div class="text-center">
        <p class="mb-3 text-gray-700">이미지를 생성하는 중입니다...</p>
        <div
          class="inline-block w-8 h-8 border-4 border-blue-200 rounded-full border-l-blue-600 animate-spin"
        ></div>
      </div>
    {:else if errorMessage}
      <div class="w-full p-4 text-red-700 rounded-lg bg-red-50">
        <p>오류 발생: {errorMessage}</p>
      </div>
    {:else if generatedImage}
      <div class="text-center">
        <img
          src={generatedImage}
          alt="생성된 이미지"
          class="max-w-full rounded-lg shadow-lg max-h-96"
        />
        <div class="mt-4">
          <a
            href={generatedImage}
            download="sd-generated-image.png"
            class="inline-flex items-center px-4 py-2 font-medium text-white transition duration-200 bg-green-600 rounded-lg hover:bg-green-700"
          >
            이미지 다운로드
          </a>
        </div>
      </div>
    {/if}
  </div>
</div>
