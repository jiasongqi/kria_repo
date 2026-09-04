---
trigger: always_on
---
# Java Code Standards

## Naming Conventions
- Class names use **PascalCase** (e.g., `UserAccountService`, `PaymentProcessor`)
- Methods and variables use **camelCase** (e.g., `getUserById`, `accountBalance`)
- Constants use **UPPER_CASE_WITH_UNDERSCORES** (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_MS`)

## Variable Declaration
- Prefer `final` modifier for immutable variables:
  final String userId = request.getUserId();
  final int MAX_RETRY_COUNT = 3;

## Documentation
- All public methods **must** include Javadoc comments:
  /**
   * Retrieves user account information by user ID.
   *
   * @param userId the unique identifier of the user
   * @return an Optional containing the account if found, or empty if not
   */
  public Optional<Account> findAccountByUserId(String userId) { ... }

## Exception Handling
- Empty catch blocks are **not allowed**; always log the exception at minimum:
  try {
      processPayment(order);
  } catch (PaymentException e) {
      log.error("Payment processing failed for order: {}", order.getId(), e);
      throw new ServiceException("Payment failed", e);
  }

## Null Safety
- Prefer `Optional` over returning `null`:
  // ✅ Preferred
  public Optional<User> findUser(String id) {
      return Optional.ofNullable(userRepository.findById(id));
  }

  // ❌ Avoid
  public User findUser(String id) {
      return userRepository.findById(id); // may return null
  }

## Collection Types
- Declare collection types using interfaces, not concrete implementations:
  // ✅ Preferred
  List<String> names = new ArrayList<>();
  Map<String, Integer> scores = new HashMap<>();
  Set<Long> ids = new HashSet<>();

  // ❌ Avoid
  ArrayList<String> names = new ArrayList<>();
  HashMap<String, Integer> scores = new HashMap<>();
