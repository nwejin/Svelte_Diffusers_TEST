<script lang="ts">
  let name: string = "";

  let age: number = 0;

  const setAge = (e: Event) => {
    age = Number((e.target as HTMLInputElement).value);
  };
</script>

<div class="p-1 bg-gray-100 w-2xl testDiv">
  <label for="name" class="text-xl">이름은 {name} 입니다.</label>
  <input
    type="text"
    id="name"
    bind:value={name}
    class="rounded-sm bg-amber-500"
  />
</div>

<div class="bg-gray-100 testDiv">
  <label for="age" class="text-xl">나이는 {age} 입니다.</label>
  <input
    type="number"
    id="age"
    value={age}
    on:input={setAge}
    class="rounded-sm bg-amber-500"
  />
</div>

<style>
  .testDiv {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 1rem;
  }
</style>
