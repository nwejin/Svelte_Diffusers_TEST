<script lang="ts">
  import { onMount } from "svelte";
  import { ContactRound } from "lucide-svelte";
  import { UserRoundPlus } from "lucide-svelte";

  // 전체 옵션
  const sexOptions = ["male", "female"];
  const ageOptions = ["10", "20", "30", "40"];
  const classOptions = ["Warrior", "Knight", "Thief", "Archer", "Wizard"];
  const personalityOptions = ["ENFP", "ISTJ", "ESTJ", "INFP"];

  // 선택 옵션
  let selectedSex = "male";
  let selectedAge = "20";
  let selectedClass = "Knight";
  let selectedPersonality = "ENFP";

  // 생성 관련
  let isLoading = false;
  let generatedImage: string | null = null;
  let errorMessage: string | null = null;

  function generatePrompt(): string {
    return `anime, background none, solo, masterpiece, best quality, 1${selectedSex}, age: ${selectedAge}, class: ${selectedClass}, personality: ${selectedPersonality}`;
  }

  let steps = 20;
  let width = 512;
  let height = 512;

  async function generateImage() {
    isLoading = true;
    generatedImage = null;
    errorMessage = null;

    try {
      const payload = {
        prompt: generatePrompt(),
        negative_prompt: "bad anatomy, worst quality, low quality, naked",
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
        console.log(data.images[0]);
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
  <!-- 이미지 영역 -->
  <div class="flex flex-col items-center justify-center mb-8 min-h-48">
    {#if isLoading}
      <div
        class="flex flex-col items-center justify-center text-center h-96 aspect-square bg-none"
      >
        <div
          class="inline-block w-20 h-20 mb-5 border-8 border-blue-200 rounded-full border-l-blue-600 animate-spin"
        ></div>
        <p class="text-gray-700">캐릭터를 생성하는 중입니다...</p>
      </div>
    {:else if !generatedImage && !errorMessage}
      <div
        class="flex items-center justify-center bg-gray-200 rounded-lg h-96 animate-pulse aspect-square"
      >
        <div class="text-gray-400 opacity-50">
          <UserRoundPlus size={300} />
        </div>
      </div>
    {:else if errorMessage}
      <div class="w-full p-4 text-red-700 rounded-lg bg-red-50">
        <p>오류 발생: {errorMessage}</p>
      </div>
    {:else if generatedImage}
      <div class="text-center">
        <img
          src={generatedImage}
          alt="생성된 캐릭터"
          class="rounded-lg shadow-lg h-96 aspect-square"
        />
        <div class="mt-4">
          <a
            href={generatedImage}
            download="sd-generated-image.png"
            class="inline-flex items-center px-4 py-2 font-medium text-white transition duration-200 bg-green-600 rounded-lg hover:bg-green-700"
          >
            저장하기
          </a>
        </div>
      </div>
    {/if}
  </div>

  <div class="p-8 mb-8 shadow-sm bg-gray-50 rounded-2xl">
    <!-- 성별 -->
    <div class="grid grid-cols-2 gap-4 mb-4">
      <!-- 성별 선택 -->
      <div>
        <label for="sex" class="block mb-1 text-sm font-medium text-gray-700"
          >성별</label
        >
        <select
          id="sex"
          bind:value={selectedSex}
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {#each sexOptions as sex}
            <option value={sex}>{sex}</option>
          {/each}
        </select>
      </div>

      <!-- 나이 선택 -->
      <div>
        <label for="age" class="block mb-1 text-sm font-medium text-gray-700"
          >나이</label
        >
        <select
          id="age"
          bind:value={selectedAge}
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {#each ageOptions as age}
            <option value={age}>{age}</option>
          {/each}
        </select>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <!-- 직업 선택 -->
      <div>
        <label for="class" class="block mb-1 text-sm font-medium text-gray-700"
          >직업</label
        >
        <select
          id="class"
          bind:value={selectedClass}
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {#each classOptions as characterClass}
            <option value={characterClass}>{characterClass}</option>
          {/each}
        </select>
      </div>

      <!-- 성격 선택 -->
      <div>
        <label
          for="personality"
          class="block mb-1 text-sm font-medium text-gray-700">성격 유형</label
        >
        <select
          id="personality"
          bind:value={selectedPersonality}
          class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {#each personalityOptions as personality}
            <option value={personality}>{personality}</option>
          {/each}
        </select>
      </div>
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
</div>
