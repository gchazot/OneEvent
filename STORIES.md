# Capability stories

- Users can register for an account. We will eventually use a SSO solution - for the time being we can use the generic Django user model.
- Admin users can create events
- Registered users can go to an event URL and register
- Discount codes can be defined in the admin and linked to one or more events
- Discount codes can be fraction (e.g. 10%) or absolute (e.g. 10 CHF)
- In the default Django auth, users belong to groups. Discounts per event can be defined for certain groups
- The registration form can support multiple exclusive registration choices with separate prices, defined dynamically in the event admin
- In addition to the registration choices, add-ons can be defined dynamically per event in the event admin
- The total price is the sum of the registration choice and add-ons minus the discounts in the currency of the event
- The admin interface includes the ability to email all registered participants of an event. These emails are stored in the event message archive
- Users can check their status (registration and registration options, payment) for all events
- Users can check the message archive for events
- Users can check their payment status
- Users can generate a PDF invoice for their event registration. The generated invoice can be downloaded or (through a button click) emailed to their registered address.
- Users can choose to use Stripe checkout to pay for registration. The success of the Stripe call should be reflected in the app. The Stripe URL is pre-defined per event registration choice.
- Admins can see how many people are registered for an event.
- Admins can limit the number of people who can register for an event.
- Admins can require a secret code for access to an event registration page.

# The following features are NOT needed

- List all events
- Administer events outside the admin interface
